package com.vincenzogulisano.usecases.linearroad;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map.Entry;
import java.util.stream.Collectors;
import java.util.TreeMap;

import org.apache.kafka.clients.producer.Producer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

public class IRLRCPUMatrix_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    private TreeMap<Long, HashMap<String, Double>> stateMeasurements;
    private long lastReportedStateMaxTS;
    List<String> relevantMetrics;
    private long valuesPerObservation;
    private final long latencyThreshold;
    private final long CPUThreshold;

    public IRLRCPUMatrix_ESC(long monitoringPeriod, Producer<String, String> producer, String separator,
            long valuesPerObservation, long latencyThreshold, long CPUThreshold) {
        super(monitoringPeriod, producer, separator, false, false);
        this.valuesPerObservation = valuesPerObservation;
        this.latencyThreshold = latencyThreshold;
        this.CPUThreshold = CPUThreshold;
        relevantMetrics = new ArrayList<>(
                Arrays.asList("injectionrate", "throughput", "outrate", "latency", "ratio", "comp", "dec",
                        "CPU-in", "CPU-agg", "CPU-out", "eventtime"));
        stateMeasurements = new TreeMap<>();
        resetVariables();

    }

    @Override
    protected void resetVariables() {
        stateMeasurements.clear();
        lastReportedStateMaxTS = -1;
    }

    /**
     * Checks if the last latency measurement (if any) in the current set exceeds a
     * predefined threshold.
     * 
     * This method iterates through all entries in {@code stateMeasurements}, which
     * could stores latency values associated with their respective timestamps. If
     * the most recent latency value meets or exceeds the threshold specified by
     * {@code latencyThreshold}, the method will return {@code true}.
     * 
     * Notice:
     * - The method will always return false if the key "latency" does not exist
     * within the map values where latency measurements are present.
     * 
     * @return {@code true} if the last latency value is greater than or equal to
     *         {@code latencyThreshold}, otherwise {@code false}.
     */
    private boolean isLatencyAboveThreshold() {
        boolean result = false;
        for (Entry<Long, HashMap<String, Double>> m : stateMeasurements.entrySet()) {
            if (m.getValue().containsKey("latency") && m.getValue().get("latency") >= latencyThreshold) {
                result = true;
            }
        }
        return result;
    }

    /**
     * Checks if the last compression measurement (if any) in the current set is
     * greater than 0
     * 
     * This method iterates through all entries in {@code stateMeasurements}, which
     * could stores compression values associated with their respective timestamps.
     * If the most recent compression value is greater than 0, the method will
     * return {@code true}.
     * 
     * Notice:
     * - The method will always return false if the key "ratio" does not exist
     * within the map values where compression measurements are present.
     * 
     * @return {@code true} if the last compression value is greater than 0,
     *         otherwise {@code false}.
     */
    private boolean isCompressionGreaterThanZero() {
        boolean result = false;
        for (Entry<Long, HashMap<String, Double>> m : stateMeasurements.entrySet()) {
            if (m.getValue().containsKey("ratio") && m.getValue().get("ratio") > 0) {
                result = true;
            }
        }
        return result;
    }

    @Override
    public String getStateMeasurementAsString() {

        logger.debug("Preparing the state measurement as string.");
        if (logger.isDebugEnabled()) {
            // Inside if to avoid substring operation cost if not needed
            logger.debug("These are the latest reports\n{}",
                    stateFormatter(stateMeasurements));
        }

        long thresholdTS = stateMeasurements.firstKey();
        logger.debug("The state will contains readings for state from ts {}.", thresholdTS);
        if (stateMeasurements.lastKey() - (thresholdTS + 1) > monitoringPeriod) {
            for (long ts : stateMeasurements.keySet()) {
                thresholdTS = ts;
                if (stateMeasurements.lastKey() - thresholdTS <= monitoringPeriod) {
                    break;
                }
            }
            logger.debug(
                    "Actually, the state will contain readings for state from {} to avoid having more than {} entries",
                    thresholdTS, monitoringPeriod);
        }

        StringBuilder logMsg = new StringBuilder();
        for (String metric : relevantMetrics) {
            for (Entry<Long, HashMap<String, Double>> entry : stateMeasurements.entrySet()) {
                if (entry.getKey() > thresholdTS) {
                    if (entry.getValue().containsKey(metric)) {
                        logMsg.append(String.format("%.2f", entry.getValue().get(metric)) + ",");
                    } else {
                        logMsg.append("-1.0,");
                    }
                }
            }
        }
        if (logger.isDebugEnabled()) {
            // Inside if to avoid substring operation cost if not needed
            logger.debug("serialized state:\n{}", logMsg.substring(0, logMsg.length() - 1));
        }
        return logMsg.substring(0, logMsg.length() - 1);
    }

    // This is the version that computes the rewards based on the latest
    // value that is not -1. If no reward can be computed, the function returns -1
    // private long computeRewardBasedOnLatestCompressionValues(List<Double> values)
    // {
    // logger.debug("Computing reward based on the latest ratio value...");
    // long reward = -1;
    // for (double value : values) {
    // if (value != -1) {
    // reward = (long) Math.round(Math.pow(100 - value, 1.5));
    // }
    // }
    // return reward;
    // }

    // This is the version that first computes the delta between first and last non
    // -1 value and if it is negative returns the respective reward. If no reward
    // can be computed, the function returns -1
    private long computeRewardBasedOnLatestCompressionValues(List<Double> values) {
        logger.debug("Computing reward based on deltas and whether the compression increased...");
        List<Double> filteredValues = values.stream().filter(v -> v != -1).collect(Collectors.toList());

        // if (filteredValues.size() >= 2 && filteredValues.getLast() -
        // filteredValues.getFirst() <= 0) {
        // return (long) Math.round(Math.pow(100 - (filteredValues.getLast() -
        // filteredValues.getFirst()), 1.5));
        // }
        if (filteredValues.size() >= 2) {
            double first = filteredValues.get(0);
            double last = filteredValues.get(filteredValues.size() - 1);
            if ((last - first) < 0) {
                return Math.round(Math.pow(Math.abs(last - first), 1.5));
            }
            return 0;
        }
        return -1;
    }

    @Override
    public long getReward() {

        logger.debug("\nComputing Reward (for timestamps greater than {})", lastReportedStateMaxTS);

        long reward = 0;

        logger.debug("Checking if new latency values above threshold exist...");
        long latency = Long.MIN_VALUE;
        double ratio = Double.MAX_VALUE;
        for (long ts : stateMeasurements.keySet()) {
            if (ts > lastReportedStateMaxTS && stateMeasurements.get(ts).containsKey("latency")
                    && stateMeasurements.get(ts).get("latency") != -1) {
                latency = (long) Math.max(stateMeasurements.get(ts).get("latency"), latency);
            }
        }
        if (latency >= latencyThreshold) {
            reward = Math.min(-1 * ((latency - 1000) / 10), -1);
            logger.debug("... they do! reporting {}", reward);
        } else {
            List<Double> latestCompressionValues = new LinkedList<>();
            for (long ts : stateMeasurements.keySet()) {
                if (ts > lastReportedStateMaxTS && stateMeasurements.get(ts).containsKey("ratio")
                        && stateMeasurements.get(ts).get("ratio") != -1) {
                    latestCompressionValues.add(stateMeasurements.get(ts).get("ratio"));
                }
            }
            long rewardFromCompression = computeRewardBasedOnLatestCompressionValues(latestCompressionValues);
            if (rewardFromCompression != -1) {
                reward = rewardFromCompression;
                logger.debug("... which is {} and means reward {}", String.format("%.2f", ratio), reward);
            }
        }

        logger.debug("Computing extra indicators (not used as of now)");
        long hiccupStretch = 0;
        long thisHiccupStretch = 0;
        for (long ts : stateMeasurements.keySet()) {
            if (ts > lastReportedStateMaxTS && (!stateMeasurements.get(ts).containsKey("eventtime")
                    || (stateMeasurements.get(ts).containsKey("eventtime")
                            && stateMeasurements.get(ts).get("eventtime") == -1))) {
                thisHiccupStretch++;
            } else {
                hiccupStretch = Math.max(hiccupStretch, thisHiccupStretch);
                thisHiccupStretch = 0;
            }
        }
        hiccupStretch = Math.max(hiccupStretch, thisHiccupStretch);
        long aboveThresholdCPU = 0;
        for (long ts : stateMeasurements.keySet()) {
            if (ts > lastReportedStateMaxTS && stateMeasurements.get(ts).containsKey("CPU-agg")) {
                if (stateMeasurements.get(ts).get("CPU-agg") >= CPUThreshold) {
                    aboveThresholdCPU++;
                }
            }
        }
        logger.debug("Longest hiccup stretch (without accounting for non-increasing event times!):{}", hiccupStretch);
        logger.debug("Above threshold CPU:{}", aboveThresholdCPU);

        lastReportedStateMaxTS = stateMeasurements.lastKey();
        logger.debug("Reward computed, lastReportedStateMaxTS updated to {}", lastReportedStateMaxTS);
        logger.debug("\n*************\n* Reward: {}\n*************\n", reward);

        HashSet<String> keysToRemove = new HashSet<>();

        // Checking if we have enought measurements
        // If more than enough and keepOnlyMonitoringPeriodData, removing them
        logger.debug("cleaning measurements");
        if (!measurements.isEmpty()) {
            for (String id_ : measurements.keySet()) {
                while (!measurements.get(id_).isEmpty()
                        && measurements.get(id_).peek().getTimestamp() <= lastReportedStateMaxTS - monitoringPeriod) {
                    measurements.get(id_).poll();
                }
                if (measurements.get(id_).isEmpty()) {
                    keysToRemove.add(id_);
                }
            }
        }
        for (String keyToRemove : keysToRemove) {
            measurements.remove(keyToRemove);
        }
        while (!stateMeasurements.isEmpty()
                && stateMeasurements.firstKey() <= lastReportedStateMaxTS - monitoringPeriod) {
            Entry<Long, HashMap<String, Double>> firstEntry = stateMeasurements.pollFirstEntry();
            logger.debug("Removed entry with ts {} from lastReportedState", firstEntry.getKey());
        }

        return reward;
    }

    @Override // In this case I am returning everything
    protected boolean valueIsToBeRegistered(String id, double value) {
        return true;
    }

    @Override
    public boolean areRewardAndNewStateMeasurementAvailable() {

        for (String metric : relevantMetrics) {
            if (measurements.containsKey(metric)) {
                for (Pair<Long, Double> measurement : measurements.get(metric)) {
                    if (!stateMeasurements.containsKey(measurement.getTimestamp())) {
                        stateMeasurements.put(measurement.getTimestamp(), new HashMap<>());
                    }
                    stateMeasurements.get(measurement.getTimestamp()).put(metric, measurement.getValue());
                }
            }
        }

        double lastEventTimeDouble = -1;
        for (Entry<Long, HashMap<String, Double>> entry : stateMeasurements.entrySet()) {
            if (entry.getValue().containsKey("eventtime")) {
                lastEventTimeDouble = Math.max(entry.getValue().get("eventtime"), lastEventTimeDouble);
            }
        }
        long lastEventTime = (long) lastEventTimeDouble;
        boolean ready = stateMeasurements.lastKey() >= clockTimeBarrier && lastEventTime >= eventTimeBarrier
                && stateMeasurements.lastKey() > lastReportedStateMaxTS && stateMeasurements.size() >= monitoringPeriod;
        logger.debug(
                "State ready based on barriers (>=)? {} - clock time:{} clock time barrier:{} event time:{} event time barrier:{} lastReportedStateMaxTS:{}, lastReportedState.size():{}",
                ready, stateMeasurements.lastKey(), clockTimeBarrier, lastEventTime, eventTimeBarrier,
                lastReportedStateMaxTS, stateMeasurements.size());

        return ready;

    }

    private String stateFormatter(TreeMap<Long, HashMap<String, Double>> newState) {

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
