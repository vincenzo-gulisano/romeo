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
import java.util.function.Consumer;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

import org.xerial.snappy.Snappy;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.Metric;
import common.metrics.Metrics;
import common.metrics.TimeMetric;
import common.tuple.RichTuple;
import component.operator.in1.aggregate.BaseKeyExtractor;
import component.operator.in1.aggregate.TimeAggregate;
import query.LiebreContext;

@SuppressWarnings("unchecked")
public class WoostAggregateWithCompression<IN extends RichTuple, OUT extends RichTuple> extends TimeAggregate<IN, OUT>
        implements Actionable, EnvironmentMonitor {

    private WoostTimeWindow<IN, OUT> aggregateWindow;
    private Map<String, WoostTimeWindow<IN, OUT>> uncompressedWins;
    private Map<String, byte[]> compressedWins;
    private long earliestWinLeftBoundary = -1;

    private Metric windowsMetric;
    private Metric tuplesMetric;
    private Metric memoryMetric;
    private Metric throughputMetric;

    private long compressionTimeThreshold;
    private Metric compressionsMetric;
    private Metric decompressionMetric;
    private TimeMetric compressionRatio;

    private Metric maxEventTimeMetric;

    private TreeMap<Long, Set<String>> tsKeys;
    private HashMap<String, Long> keyLatestTs;

    // Used for compression
    private ByteArrayOutputStream baos;
    private ObjectOutputStream oos;

    // Used to retrieve D updated
    private ConcurrentLinkedQueue<Long> dUpdates;
    // private List<FileMonitor> fileMonitors;
    private String statsFolder;
    private StatReporter statReporter;
    private EnvironmentMonitor source;
    private EnvironmentMonitor sink;

    public WoostAggregateWithCompression(
            String id,
            int instance,
            int parallelismDegree,
            long windowSize,
            long windowSlide,
            WoostTimeWindow<IN, OUT> aggregateWindow,
            long compressionTimeThreshold,
            String statsFolder,
            EnvironmentMonitor source,
            EnvironmentMonitor sink) {
        super(id, instance, parallelismDegree, windowSize, windowSlide, aggregateWindow, new BaseKeyExtractor<IN>());
        uncompressedWins = new HashMap<>();
        compressedWins = new HashMap<>();
        this.aggregateWindow = aggregateWindow;
        this.compressionTimeThreshold = compressionTimeThreshold;

        tsKeys = new TreeMap<>();
        keyLatestTs = new HashMap<>();

        this.dUpdates = new ConcurrentLinkedQueue<>();
        // this.fileMonitors = new LinkedList<>();
        this.statsFolder = statsFolder;
        // this.fileMonitors.add(new FileMonitor("eventtime", statsFolder +
        // File.separator + "eventtime.max.csv"));
        this.source = source;
        this.sink = sink;

    }

    @Override
    public void enable() {

        System.out.println("Enabling statistiscs");

        super.enable();
        windowsMetric.enable();
        tuplesMetric.enable();
        memoryMetric.enable();
        compressionsMetric.enable();
        decompressionMetric.enable();
        maxEventTimeMetric.enable();
        compressionRatio.enable();
        throughputMetric.enable();

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

    public List<OUT> processTupleIn1(IN t) {

        // Check for D updates
        while (!dUpdates.isEmpty()) {
            Long d = dUpdates.poll();
            if (d != null) {
                compressionTimeThreshold = d;
                System.out.println("Compression threshold updated to " + compressionTimeThreshold);
            }
        }

        // Prepare statistics vars
        memoryChange = 0;
        decompressions = 0;
        tuplesChange = 0;
        compressions = 0;
        windowsChange = 0;

        // Create result
        List<OUT> result = new LinkedList<OUT>();

        // Check timestamps are not decreasing
        checkIncreasingTimestamps(t);

        // Extract tuple info
        latestTimestamp = t.getTimestamp();
        long tL = getEarliestWinStartTS(latestTimestamp);
        String k = keyExtractor.getKey(t);

        while (earliestWinLeftBoundary != -1 && earliestWinLeftBoundary < tL) {

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

        // Update metrics
        memoryMetric.record(memoryChange);
        decompressionMetric.record(decompressions);
        tuplesMetric.record(tuplesChange);
        compressionsMetric.record(compressions);
        maxEventTimeMetric.record(t.getTimestamp());
        windowsMetric.record(windowsChange);
        compressionRatio.record((long) (((double) uncompressedWins.size() * 100)
                / ((double) compressedWins.size() + (double) uncompressedWins.size())));

        throughputMetric.record(1);

        return result;
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

    @Override
    public void changeD(long v) {
        System.out.println("Storing change request to d:" + v);
        dUpdates.add(v);
    }

    @Override
    public void setStatReporter(StatReporter reporter) {
        System.out.println("Setting stat reporter");
        this.statReporter = reporter;

        System.out.println("Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        consumers.put("windows", x -> reporter.report((long) x[0], "windows", ((Long) x[1]).doubleValue()));
        consumers.put("tuples", x -> reporter.report((long) x[0], "tuples", ((Long) x[1]).doubleValue()));
        consumers.put("memory", x -> reporter.report((long) x[0], "memory", ((Long) x[1]).doubleValue()));
        consumers.put("comp", x -> reporter.report((long) x[0], "comp", ((Long) x[1]).doubleValue()));
        consumers.put("ratio", x -> reporter.report((long) x[0], "ratio", ((Long) x[1]).doubleValue()));
        consumers.put("dec", x -> reporter.report((long) x[0], "dec", ((Long) x[1]).doubleValue()));
        consumers.put("eventtime", x -> reporter.report((long) x[0], "eventtime", ((Long) x[1]).doubleValue()));
        consumers.put("throughput", x -> reporter.report((long) x[0], "throughput", ((Long) x[1]).doubleValue()));

        // This is not good, consumers should be registered in their own classes
        consumers.put("injectionrate", x -> reporter.report((long) x[0], "injectionrate", ((Long) x[1]).doubleValue()));
        consumers.put("outrate", x -> reporter.report((long) x[0], "outrate", ((Long) x[1]).doubleValue()));
        consumers.put("latency", x -> reporter.report((long) x[0], "latency", ((Long) x[1]).doubleValue()));

        System.out.println("Setting metrics type in Liebre");
        LiebreContext.setUserMetrics(Metrics.fileAndConsumer(statsFolder, consumers));

        System.out.println("Creating statistics");
        windowsMetric = LiebreContext.userMetrics().newTotalCountMetric("windows", "count");
        tuplesMetric = LiebreContext.userMetrics().newTotalCountMetric("tuples", "count");
        memoryMetric = LiebreContext.userMetrics().newTotalCountMetric("memory", "size");
        compressionsMetric = LiebreContext.userMetrics().newTotalCountMetric("comp", "count");
        compressionRatio = LiebreContext.userMetrics().newAverageTimeMetric("ratio", "percent");
        decompressionMetric = LiebreContext.userMetrics().newTotalCountMetric("dec", "count");
        maxEventTimeMetric = LiebreContext.userMetrics().newTotalMaxMetric("eventtime", "max");
        throughputMetric = LiebreContext.userMetrics().newCountPerSecondMetric("throughput", "count");

        // Now set metric reporter to source and sink too
        source.setStatReporter(reporter);
        sink.setStatReporter(reporter);

    }

}
