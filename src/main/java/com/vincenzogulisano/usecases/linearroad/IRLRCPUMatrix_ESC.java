package com.vincenzogulisano.usecases.linearroad;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.TreeMap;

import org.apache.kafka.clients.producer.Producer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

/**
 * This is the one that has been used since Exp3
 */

public class IRLRCPUMatrix_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    // private long IR; // Input Rate
    // private long L; // Latency
    // private long lastLTimestamp;
    // private double R; // Rate
    // private double CPU;
    // private long lastTS;
    // private long ts;

    // private double[][] measurement;
    // private TreeMap<Long, HashMap<String, Double>> prevReportedState;

    private TreeMap<Long, HashMap<String, Double>> lastReportedState;
    private long lastReportedStateMaxTS;
    List<String> relevantMetrics;
    private long valuesPerObservation;
    private final long latencyThreshold = 1000;
    private final long CPUThreshold = 80;

    public IRLRCPUMatrix_ESC(long monitoringPeriod, Producer<String, String> producer, String separator,
            long valuesPerObservation) {
        super(monitoringPeriod, producer, separator, false);
        this.valuesPerObservation = valuesPerObservation;
        relevantMetrics = new ArrayList<>(
                Arrays.asList("injectionrate", "throughput", "outrate", "latency", "ratio", "comp", "dec",
                        "CPU-in", "CPU-agg", "CPU-out", "eventtime"));
        resetVariables();

    }

    protected void resetVariables() {
        // IR = -1;
        // L = -1;
        // lastLTimestamp = -1;
        // R = -1;
        // CPU = -1;
        // prevReportedState = new TreeMap<>();
        lastReportedState = new TreeMap<>();
        lastReportedStateMaxTS = -1;
    }

    @Override
    public String getStateMeasurementAsString() {
        String logMsg = "";
        for (String metric : relevantMetrics) {
            for (long ts : lastReportedState.keySet()) {
                if (lastReportedState.get(ts).containsKey(metric)) {
                    logMsg += String.format("%.2f", lastReportedState.get(ts).get(metric)) + ",";
                } else {
                    logMsg += "-1.0,";
                }
            }
        }
        // Remove the last comma
        return logMsg.substring(0, logMsg.length() - 2);
    }

    @Override
    public long getReward() {

        logger.debug("\nComputing Reward (for timestamps from {})", lastReportedStateMaxTS + 1);

        long reward = 0;

        logger.debug("Checking if new latency values above threshold exist...");
        long latency = Long.MIN_VALUE;
        double ratio = Double.MAX_VALUE;
        for (long ts : lastReportedState.keySet()) {
            if (ts > lastReportedStateMaxTS && lastReportedState.get(ts).containsKey("latency")
                    && lastReportedState.get(ts).get("latency") != -1) {
                latency = (long) Math.max(lastReportedState.get(ts).get("latency"), latency);
            }
        }
        if (latency >= latencyThreshold) {
            reward = Math.min(-1 * ((latency - 1000) / 10), -1);
            logger.debug("... they do! reporting {}", reward);
        } else {
            logger.debug("Retrieving the latest ratio value...");
            for (long ts : lastReportedState.keySet()) {
                if (ts > lastReportedStateMaxTS && lastReportedState.get(ts).containsKey("ratio")
                        && lastReportedState.get(ts).get("ratio") != -1) {
                    ratio = lastReportedState.get(ts).get("ratio");
                }
            }
            if (ratio != Double.MAX_VALUE) {
                reward = (long) Math.round(Math.pow(100 - ratio, 1.5));
                logger.debug("... which is {} and means reward {}", String.format("%.2f", ratio), reward);
            }
        }

        logger.debug("Computing extra indicators (not used as of now)");
        long hiccupStretch = 0;
        long thisHiccupStretch = 0;
        for (long ts : lastReportedState.keySet()) {
            if (ts > lastReportedStateMaxTS && (!lastReportedState.get(ts).containsKey("eventtime")
                    || (lastReportedState.get(ts).containsKey("eventtime")
                            && lastReportedState.get(ts).get("eventtime") == -1))) {
                thisHiccupStretch++;
            } else {
                hiccupStretch = Math.max(hiccupStretch, thisHiccupStretch);
                thisHiccupStretch = 0;
            }
        }
        hiccupStretch = Math.max(hiccupStretch, thisHiccupStretch);
        long aboveThresholdCPU = 0;
        for (long ts : lastReportedState.keySet()) {
            if (ts > lastReportedStateMaxTS && lastReportedState.get(ts).containsKey("CPU-agg")) {
                if (lastReportedState.get(ts).get("CPU-agg") >= CPUThreshold) {
                    aboveThresholdCPU++;
                }
            }
        }
        logger.debug("Longest hiccup stretch (without accounting for non-increasing event times!):{}", hiccupStretch);
        logger.debug("Above threshold CPU:{}", aboveThresholdCPU);

        lastReportedStateMaxTS = lastReportedState.lastKey();
        logger.debug("Reward computed, lastReportedStateMaxTS updated to {}", lastReportedStateMaxTS);
        logger.debug("\n*************\n* Reward: {}\n*************\n", reward);

        return reward;
    }

    @Override // In this case I am returning everything
    protected boolean valueIsToBeRegistered(String id, double value) {
        return true;
    }

    @Override
    public boolean computeStateMeasurementAndReward() {

        // logger.debug("Checking if state measurement and reward are available");

        lastReportedState = new TreeMap<>();

        // logger.debug("Trying to find the min and max timestamps of the relevant
        // metrics {}", relevantMetrics);
        // long minTS = Long.MAX_VALUE;
        // long maxTS = Long.MIN_VALUE;
        // for (String metric : relevantMetrics) {
        // if (measurements.containsKey(metric)) {
        // logger.debug("Relevant measuremet: {}", measurements.get(metric));
        // minTS = measurements.get(metric).getFirst().getTimestamp() < minTS
        // ? measurements.get(metric).getFirst().getTimestamp()
        // : minTS;
        // maxTS = measurements.get(metric).getLast().getTimestamp() > maxTS
        // ? measurements.get(metric).getLast().getTimestamp()
        // : maxTS;
        // }
        // }
        // if (minTS == Long.MAX_VALUE || maxTS == Long.MIN_VALUE) {
        // logger.fatal("Trying to find the min and max timestamps of the relevant
        // metrics {}", relevantMetrics);
        // throw new RuntimeException("Could not find a single statistic for the
        // relevant metrics " + relevantMetrics);
        // }
        // if (maxTS - minTS < valuesPerObservation - 1) {
        // // logger.debug("Cannot produce measurements, since I do not have {} values
        // per
        // // observation",
        // // valuesPerObservation);
        // return false;
        // }

        // if (minTS <= maxTS - valuesPerObservation) {
        // minTS = maxTS - valuesPerObservation + 1;
        // // logger.debug("There are more values than needed, changed minTS to {}",
        // // minTS);
        // }

        // logger.debug("MinTS={} MaxTS={}", minTS, maxTS);
        // logger.debug("Creating a 2d matrix of {}x{} entries and populating it",
        // relevantMetrics.size(),
        // (int) (maxTS - minTS + 1));
        // measurement = new double[relevantMetrics.size()][(int) (maxTS - minTS + 1)];
        // for (int i = 0; i < measurement.length; i++) {
        // for (int j = 0; j < measurement[i].length; j++) {
        // measurement[i][j] = -1;
        // }
        // }
        for (String metric : relevantMetrics) {
            if (measurements.containsKey(metric)) {
                for (Pair<Long, Double> measurement : measurements.get(metric)) {
                    if (!lastReportedState.containsKey(measurement.getTimestamp())) {
                        lastReportedState.put(measurement.getTimestamp(), new HashMap<>());
                    }
                    lastReportedState.get(measurement.getTimestamp()).put(metric, measurement.getValue());
                }
            }
        }

        // Remove extra values
        if (!lastReportedState.isEmpty()) {
            while (lastReportedState.lastKey() - lastReportedState.firstKey() > valuesPerObservation) {
                lastReportedState.pollFirstEntry();
            }
        }

        // for (String id_ : measurements.keySet()) {
        // if (id_.equals("injectionrate") || id_.equals("ratio") ||
        // id_.equals("CPU-agg")) {
        // double sum = 0.0;
        // double count = 0.0;
        // for (Pair<Long, Double> v : measurements.get(id_)) {
        // if (v.getValue() != -1) {
        // sum += v.getValue();
        // count++;
        // }
        // }
        // double avg = count > 0 ? sum / count : -1;
        // switch (id_) {
        // case "injectionrate":
        // IR = (long) avg;
        // // logger.debug("registered injectionrate {}", IR);
        // break;
        // case "ratio":
        // R = avg;
        // // logger.debug("registered ratio {}", R);
        // break;
        // case "CPU-agg":
        // CPU = avg;
        // // logger.debug("registered cpu {}", CPU);
        // break;
        // default:
        // break;
        // }
        // }
        // if (id_.equals("latency")) {
        // L = -1;
        // for (Pair<Long, Double> v : measurements.get(id_)) {
        // if (v.getTimestamp() > lastLTimestamp) {
        // L = (long) (v.getValue() > L ? v.getValue() : L);
        // lastLTimestamp = v.getTimestamp();
        // // logger.debug("Found a newer latency for ts:{} and value:{}",
        // lastLTimestamp,
        // // L);
        // }
        // }
        // // logger.debug("registered latency {}", L);
        // }
        // }

        // Notice I set lastTS + 1 to make sure I send the state when all the
        // measurements for the same second have been received

        long lastEventTime = (long) (lastReportedState.lastEntry().getValue().containsKey("eventtime")
                ? lastReportedState.lastEntry().getValue().get("eventtime")
                : -1);
        boolean ready = lastReportedState.lastKey() >= clockTimeBarrier && lastEventTime >= eventTimeBarrier;
        logger.debug(
                    "State ready based on barriers (>=)? {} - clock time:{} clock time barrier:{} event time:{} event time barrier:{}",
                    ready, lastReportedState.lastKey(), clockTimeBarrier, lastEventTime, eventTimeBarrier);
        if (ready) {
            
            logger.debug("This is the resulting matrix\n{}",
                    stateFormatter(lastReportedState, null));
            // logger.debug("This is the reward\n{}",
            // getReward());
            // prevReportedState = lastReportedState;
        } else {

        }
        return ready;

    }

    private String stateFormatter(TreeMap<Long, HashMap<String, Double>> newState,
            TreeMap<Long, HashMap<String, Double>> prevState) {

        String formattedState = "";

        int columns = (int) (newState.lastKey() - newState.firstKey()) + 2;
        int rows = relevantMetrics.size() + 1;

        String[][] data = new String[rows][columns];
        data[0][0] = "";
        for (long ts : newState.keySet()) {
            int column = (int) (ts - newState.firstKey()) + 1;
            data[0][column] = "" + ts;
            for (int i = 0; i < relevantMetrics.size(); i++) {
                String metric = relevantMetrics.get(i);
                data[i + 1][0] = metric;
                // if (prevState.containsKey(ts)) {
                // if (prevState.get(ts).containsKey(metric)
                // && prevState.get(ts).get(metric) != newState.get(ts).get(metric)) {
                // data[i + 1][column] = "! ";
                // } else {
                // data[i + 1][column] = "- ";
                // }
                // } else {
                // data[i + 1][column] = "* ";
                // }
                if (newState.get(ts).containsKey(metric)) {
                    data[i + 1][column] = String.format("%.2f", newState.get(ts).get(metric));
                } else {
                    data[i + 1][column] = "-1.0";
                }
            }

        }

        // Calculate the maximum width for each column
        int[] maxWidths = new int[data[0].length];
        for (String[] row : data) {
            for (int i = 0; i < row.length; i++) {
                maxWidths[i] = Math.max(maxWidths[i], row[i].length());
            }
        }

        // Print the data with aligned columns
        for (String[] row : data) {
            for (int i = 0; i < row.length; i++) {
                formattedState += String.format("%-" + (maxWidths[i] + 2) + "s", row[i]); // +2 for padding
            }
            formattedState += "\n";
        }

        return formattedState;

    }

}
