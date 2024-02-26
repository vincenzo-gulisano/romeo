package com.vincenzogulisano.woost;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.Map.Entry;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Consumer;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.xerial.snappy.Snappy;

import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.Metric;
import common.metrics.TimeMetric;
import common.tuple.RichTuple;
import common.util.Util;
import component.operator.in1.aggregate.BaseKeyExtractor;
import component.operator.in1.aggregate.TimeAggregate;
import query.LiebreContext;

@SuppressWarnings("unchecked")
public class WoostAggregateWithCompression<IN extends RichTuple, OUT extends RichTuple> extends TimeAggregate<IN, OUT> {

    private WoostTimeWindow<IN, OUT> aggregateWindow;
    private Map<String, WoostTimeWindow<IN, OUT>> uncompressedWins;
    private Map<String, byte[]> compressedWins;
    private long earliestWinLeftBoundary;

    private Metric windowsMetric;
    private Metric tuplesMetric;
    private Metric memoryMetric;
    private Metric throughputMetric;
    private Metric outputtMetric;

    private long compressionTimeThreshold;
    private Metric compressionsMetric;
    private Metric decompressionMetric;
    private TimeMetric compressionRatio;

    private Metric maxEventTimeMetric;

    // This new field is added to keep track of the latest event time
    // It is set to -1 upon reset
    // TODO It is probably redundant, latestTimestamp might do
    private volatile long latestEventTime;

    private TreeMap<Long, Set<String>> tsKeys;
    private HashMap<String, Long> keyLatestTs;

    // Used for compression
    private ByteArrayOutputStream baos;
    private ObjectOutputStream oos;

    private ConcurrentLinkedQueue<Long> dUpdates;

    public Logger logger = LogManager.getLogger();

    private volatile boolean resetRequest;
    private volatile boolean resetAck;
    // Temp
    private volatile boolean firstCallAfterReset;
    // private Lock resetLock;

    public WoostAggregateWithCompression(
            String id,
            int instance,
            int parallelismDegree,
            long windowSize,
            long windowSlide,
            WoostTimeWindow<IN, OUT> aggregateWindow,
            long compressionTimeThreshold,
            String statsFolder) {
        super(id, instance, parallelismDegree, windowSize, windowSlide, aggregateWindow, new BaseKeyExtractor<IN>());

        this.aggregateWindow = aggregateWindow;
        this.compressionTimeThreshold = compressionTimeThreshold;
        this.dUpdates = new ConcurrentLinkedQueue<>();

        this.resetRequest = false;
        this.resetAck = false;
        this.firstCallAfterReset = false;
        // this.resetLock = new ReentrantLock();

    }

    public void reset() {
        logger.debug("Registering reset request");
        resetAck = false;
        resetRequest = true;
        firstCallAfterReset = false;
        // resetLock.lock();
        // logger.debug("Got the reset lock");
        logger.debug("{} tuples in input stream", getInput().size());
        while (getInput().size() > 0 || inProcess) {
            logger.debug("Tuples being processed ({})", getInput().size());
            Util.sleep(500);
        }
        // if (getInput().size() == 0) {
        logger.debug("No tuples in the input stream, resetting");
        if (inProcess) {
            logger.debug("In process though... so we wait");
            while (inProcess) {
                Util.sleep(50);
            }
            logger.debug("Process complete");
        } else {
            logger.debug("and not processing tuples");
        }
        internalReset();
        // } else {
        // logger.debug("There exist tuples in the input stream, deferring the reset to
        // main thread");
        // }
        // resetLock.unlock();

    }

    private void internalReset() {
        logger.debug("Clearing {} tuples in input stream", getInput().size());
        getInput().clear();
        logger.debug("Resetting windows");
        uncompressedWins = new HashMap<>();
        compressedWins = new HashMap<>();
        tsKeys = new TreeMap<>();
        keyLatestTs = new HashMap<>();
        earliestWinLeftBoundary = -1;
        latestEventTime = -1;
        windowsMetric.reset();
        tuplesMetric.reset();
        memoryMetric.reset();
        compressionsMetric.reset();
        decompressionMetric.reset();
        maxEventTimeMetric.reset();
        compressionRatio.reset();
        throughputMetric.reset();
        outputtMetric.reset();
        logger.debug("Acking back to SPE");
        resetAck = true;
        resetRequest = false;
        firstCallAfterReset = true;
    }

    public boolean getResetAck() {
        return resetAck;
    }

    @Override
    public void enable() {

        logger.debug("Enabling statistiscs");

        super.enable();
        windowsMetric.enable();
        tuplesMetric.enable();
        memoryMetric.enable();
        compressionsMetric.enable();
        decompressionMetric.enable();
        maxEventTimeMetric.enable();
        compressionRatio.enable();
        throughputMetric.enable();
        outputtMetric.enable();

    }

    @Override
    public void disable() {
        super.disable();
        windowsMetric.disable();
        tuplesMetric.disable();
        memoryMetric.disable();
        compressionsMetric.disable();
        decompressionMetric.disable();
        maxEventTimeMetric.disable();
        compressionRatio.disable();
        throughputMetric.disable();
        outputtMetric.disable();
    }

    // Iterators and entries used by the processTupleIn1 function
    Iterator<Entry<String, byte[]>> i1;
    Entry<String, byte[]> e1;
    WoostTimeWindow<IN, OUT> wToDecompress;
    Iterator<Entry<String, WoostTimeWindow<IN, OUT>>> i2;
    Entry<String, WoostTimeWindow<IN, OUT>> e2;
    Iterator<Map.Entry<Long, Set<String>>> compressionIt;
    Map.Entry<Long, Set<String>> compressionE;
    WoostTimeWindow<IN, OUT> wToCompress;

    // statistics updates
    long memoryChange;
    long decompressions;
    long compressions;
    long tuplesChange;
    long windowsChange;

    private volatile boolean inProcess = false;

    public List<OUT> processTupleIn1(IN t) {

        if (firstCallAfterReset) {
            logger.debug("First invocation of processTupleIn1 after the reset");
            logger.debug("{} tuples in input stream to be processed", getInput().size());
        }

        // if (resetRequest) {
        // logger.debug("Processing reset request");
        // resetLock.lock();
        // logger.debug("Got the reset lock");
        // internalReset();
        // resetLock.unlock();
        // }

        inProcess = true;

        // Check for D updates
        while (!dUpdates.isEmpty()) {
            logger.debug("dUpdate is not empty");
            Long d = dUpdates.poll();
            if (d != null) {
                compressionTimeThreshold = d;
                logger.debug("Compression threshold updated to " + compressionTimeThreshold);
            }
            Util.sleep(500);
        }

        // Prepare statistics vars
        memoryChange = 0;
        decompressions = 0;
        tuplesChange = 0;
        compressions = 0;
        windowsChange = 0;

        // Create result
        List<OUT> result = new LinkedList<OUT>();

        // Extract tuple info
        latestTimestamp = t.getTimestamp();
        long tL = getEarliestWinStartTS(latestTimestamp);
        String k = keyExtractor.getKey(t);

        if (firstCallAfterReset) {
            logger.debug("The condition to enter the output production loop is {}",
                    (earliestWinLeftBoundary != -1 && earliestWinLeftBoundary < tL));
        }

        while (earliestWinLeftBoundary != -1 && earliestWinLeftBoundary < tL) {

            if (firstCallAfterReset) {
                logger.debug("earliestWinLeftBoundary is {}", earliestWinLeftBoundary);
                logger.debug("tL is {}", tL);
            }

            // Produce results for compressed (if any)
            i1 = compressedWins.entrySet().iterator();
            while (i1.hasNext()) {
                e1 = i1.next();

                memoryChange -= e1.getValue().length;

                // Decompress
                try {
                    wToDecompress = (WoostTimeWindow<IN, OUT>) new ObjectInputStream(
                            new ByteArrayInputStream(Snappy.uncompress(e1.getValue()))).readObject();
                    decompressions++;
                } catch (ClassNotFoundException | IOException e1) {
                    e1.printStackTrace();
                }

                // Get output
                wToDecompress.setLatestStimulus(t.getStimulus());
                OUT outT = wToDecompress.getAggregatedResult();
                if (outT != null) {
                    outputtMetric.record(1);
                    result.add(outT);
                }

                // Slide
                tuplesChange -= wToDecompress.getNumberOfTuples();
                wToDecompress.slideTo(earliestWinLeftBoundary + WA);
                tuplesChange += wToDecompress.getNumberOfTuples();

                // Remove or compress again
                if (wToDecompress.isEmpty()) {
                    i1.remove();
                    windowsChange--;
                } else {

                    try {
                        baos = new ByteArrayOutputStream();
                        oos = new ObjectOutputStream(baos);
                        oos.writeObject(wToDecompress);
                        oos.close();
                        e1.setValue(Snappy.compress(baos.toByteArray()));
                    } catch (IOException exception) {
                        exception.printStackTrace();
                    }

                    memoryChange += e1.getValue().length;
                    compressions++;
                }

            }

            // Produce results for uncompressed (if any)
            i2 = uncompressedWins.entrySet().iterator();
            while (i2.hasNext()) {
                e2 = i2.next();

                memoryChange -= e2.getValue().getSizeInBytes();

                // Get output
                e2.getValue().setLatestStimulus(t.getStimulus());
                OUT outT = e2.getValue().getAggregatedResult();
                if (outT != null) {
                    outputtMetric.record(1);
                    result.add(outT);
                }

                // Slide
                tuplesChange -= e2.getValue().getNumberOfTuples();
                e2.getValue().slideTo(earliestWinLeftBoundary + WA);
                tuplesChange += e2.getValue().getNumberOfTuples();

                // Remove or compress again
                if (e2.getValue().isEmpty()) {

                    tsKeys.get(keyLatestTs.get(e2.getKey())).remove(e2.getKey());
                    keyLatestTs.remove(e2.getKey());

                    i2.remove();
                    windowsChange--;
                } else {
                    memoryChange += e2.getValue().getSizeInBytes();
                }

            }

            // At this point, all windows at earliestWinLeftBoundary are done, so we can
            // update tsKeys
            tsKeys.remove(earliestWinLeftBoundary);

            earliestWinLeftBoundary += tL;
        }

        // Add contribution of this tuple and update metrics
        WoostTimeWindow<IN, OUT> w = getWindow(tL, k);
        memoryChange -= w.getSizeInBytes();
        w.add(t);
        tuplesChange++;
        memoryChange += w.getSizeInBytes();

        // if the key was already observed before, it has been
        // stored associated to its previous timestamp, so that can be
        // removed
        if (keyLatestTs.containsKey(k)) {
            tsKeys.get(keyLatestTs.get(k)).remove(k);
        }
        // Now store the latest key and ts pair in both variables
        keyLatestTs.put(k, latestTimestamp);
        if (!tsKeys.containsKey(latestTimestamp)) {
            tsKeys.put(latestTimestamp, new HashSet<>());
        }
        tsKeys.get(latestTimestamp).add(k);

        // Compress early windows (if any)
        compressionIt = tsKeys.entrySet().iterator();
        while (compressionIt.hasNext()) {
            compressionE = compressionIt.next();
            if (latestTimestamp - compressionE.getKey() >= compressionTimeThreshold) {

                for (String wK : compressionE.getValue()) {

                    wToCompress = uncompressedWins.get(wK);
                    uncompressedWins.remove(wK); // Added while writing pseudocode, check if correct!
                    // Move to compressed windows and update memory metric
                    memoryChange -= wToCompress.getSizeInBytes();

                    try {
                        baos = new ByteArrayOutputStream();
                        oos = new ObjectOutputStream(baos);
                        oos.writeObject(wToCompress);
                        oos.close();
                        // assert (!compressedWins.containsKey(wK));
                        compressedWins.put(wK, Snappy.compress(baos.toByteArray()));
                        memoryChange += compressedWins.get(wK).length;

                        compressions++;
                    } catch (IOException exception) {
                        exception.printStackTrace();
                    }

                    // Remove from keyLatestTs, because now they are compressed
                    keyLatestTs.remove(wK);
                }

                compressionIt.remove(); // Remove the current entry safely
            } else {
                break;
            }
        }

        earliestWinLeftBoundary = tL;
        if (firstCallAfterReset) {
            logger.debug("Now updating metrics");
        }
        // Update metrics
        latestEventTime = t.getTimestamp();
        memoryMetric.record(memoryChange);
        decompressionMetric.record(decompressions);
        tuplesMetric.record(tuplesChange);
        compressionsMetric.record(compressions);
        maxEventTimeMetric.record(latestEventTime);
        windowsMetric.record(windowsChange);
        compressionRatio.record((long) (((double) uncompressedWins.size() * 100)
                / ((double) compressedWins.size() + (double) uncompressedWins.size())));

        throughputMetric.record(1);

        inProcess = false;
        if (firstCallAfterReset) {
            logger.debug("Exiting");
            firstCallAfterReset = false;
        }

        return result;
    }

    /**
     * Returns the latest event time processed by the Aggregate. Or -1 if no tuple
     * has been processed (possibly after a reset)
     * 
     * @return The latest event time
     */
    public long getLatestEventTime() {
        return latestEventTime;
    }

    private WoostTimeWindow<IN, OUT> getWindow(long tL, String k) {
        WoostTimeWindow<IN, OUT> result = null;
        if (compressedWins.containsKey(k)) {
            // Decompress

            memoryChange -= compressedWins.get(k).length;

            try {
                result = (WoostTimeWindow<IN, OUT>) new ObjectInputStream(
                        new ByteArrayInputStream(Snappy.uncompress(compressedWins.get(k)))).readObject();
            } catch (ClassNotFoundException | IOException e1) {
                e1.printStackTrace();
            }

            // long winMemBeforeDecompress = result.getSizeInBytes();
            // result.decompress();
            memoryChange += result.getSizeInBytes();

            decompressions++;
            // assert (!uncompressedWins.containsKey(k));
            uncompressedWins.put(k, result);
            compressedWins.remove(k);
        } else if (uncompressedWins.containsKey(k)) {
            result = uncompressedWins.get(k);
        } else {
            result = aggregateWindow.woostFactory();
            result.setKey(k);
            result.setInstanceNumber(instance);
            result.setParallelismDegree(parallelismDegree);
            result.slideTo(tL);
            uncompressedWins.put(k, result);
            windowsChange++;

        }
        return result;
    }

    public long changeD(long v) {
        logger.debug("Storing change request to d:" + v);
        dUpdates.add(v);
        return latestEventTime;
    }

    public HashMap<String, Consumer<Object[]>> setStatReporter(StatReporter reporter) {
        logger.debug("Agg - Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        consumers.put("windows", x -> reporter.report((long) x[0], "windows", ((Long) x[1]).doubleValue()));
        consumers.put("tuples", x -> reporter.report((long) x[0], "tuples", ((Long) x[1]).doubleValue()));
        consumers.put("memory", x -> reporter.report((long) x[0], "memory", ((Long) x[1]).doubleValue()));
        consumers.put("comp", x -> reporter.report((long) x[0], "comp", ((Long) x[1]).doubleValue()));
        consumers.put("ratio", x -> reporter.report((long) x[0], "ratio", ((Long) x[1]).doubleValue()));
        consumers.put("dec", x -> reporter.report((long) x[0], "dec", ((Long) x[1]).doubleValue()));
        consumers.put("eventtime", x -> reporter.report((long) x[0], "eventtime", ((Long) x[1]).doubleValue()));
        consumers.put("throughput", x -> reporter.report((long) x[0], "throughput", ((Long) x[1]).doubleValue()));
        consumers.put("agg-output", x -> reporter.report((long) x[0], "agg-output", ((Long) x[1]).doubleValue()));

        return consumers;

    }

    public void createStatistics() {
        logger.debug("Agg - Creating statistics");
        windowsMetric = LiebreContext.userMetrics().newTotalCountMetric("windows", "count");
        tuplesMetric = LiebreContext.userMetrics().newTotalCountMetric("tuples", "count");
        memoryMetric = LiebreContext.userMetrics().newTotalCountMetric("memory", "size");
        compressionsMetric = LiebreContext.userMetrics().newTotalCountMetric("comp", "count");
        compressionRatio = LiebreContext.userMetrics().newAverageTimeMetric("ratio", "percent");
        decompressionMetric = LiebreContext.userMetrics().newTotalCountMetric("dec", "count");
        maxEventTimeMetric = LiebreContext.userMetrics().newTotalMaxMetric("eventtime", "max");
        throughputMetric = LiebreContext.userMetrics().newCountPerSecondMetric("throughput", "count");
        outputtMetric = LiebreContext.userMetrics().newCountPerSecondMetric("agg-output", "count");
    }

}
