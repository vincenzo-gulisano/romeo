package com.vincenzogulisano.usecases.linearroad;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map.Entry;
import java.util.TreeMap;

import org.apache.kafka.clients.producer.Producer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

public class IRLRCPUMatrix_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    private TreeMap<Long, HashMap<String, Double>> lastReportedState;
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
        lastReportedState = new TreeMap<>();
        resetVariables();

    }

    protected void resetVariables() {
        lastReportedState.clear();
        lastReportedStateMaxTS = -1;
    }

    @Override
    public String getStateMeasurementAsString() {

        logger.debug("Preparing the state measurement as string.");
        logger.debug("These are the latest reports\n{}",
                stateFormatter(lastReportedState));
        // if (lastReportedStateMaxTS == -1) {
        //     lastReportedStateMaxTS = lastReportedState.firstKey() - 1;
        //     logger.debug("Set lastReportedStateMaxTS to {} because it was -1", lastReportedStateMaxTS);
        // }
        long thresholdTS = lastReportedState.firstKey();
        logger.debug("The state will contains readings for state from ts {}.", thresholdTS);
        if (lastReportedState.lastKey() - (thresholdTS + 1) > monitoringPeriod) {
            for(long ts : lastReportedState.keySet()) {
                thresholdTS = ts;
                if (lastReportedState.lastKey() - thresholdTS <= monitoringPeriod) {
                    break;
                }
            }
            logger.debug(
                    "Actually, the state will contain readings for state from {} to avoid having more than {} entries",
                    thresholdTS, monitoringPeriod);
        }

        String logMsg = "";
        for (String metric : relevantMetrics) {
            for (long ts : lastReportedState.keySet()) {
                if (ts > thresholdTS) {
                    if (lastReportedState.get(ts).containsKey(metric)) {
                        logMsg += String.format("%.2f", lastReportedState.get(ts).get(metric)) + ",";
                    } else {
                        logMsg += "-1.0,";
                    }
                }
            }
        }
        // Remove the last comma
        logger.debug("serialized state:\n{}", logMsg.substring(0, logMsg.length() - 1));
        return logMsg.substring(0, logMsg.length() - 1);
    }

    @Override
    public long getReward() {

        logger.debug("\nComputing Reward (for timestamps greater than {})", lastReportedStateMaxTS);

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
        while (!lastReportedState.isEmpty()
                && lastReportedState.firstKey() <= lastReportedStateMaxTS - monitoringPeriod) {
            Entry<Long, HashMap<String, Double>> firstEntry = lastReportedState.pollFirstEntry();
            logger.debug("Removed entry with ts {} from lastReportedState", firstEntry.getKey());
        }

        return reward;
    }

    @Override // In this case I am returning everything
    protected boolean valueIsToBeRegistered(String id, double value) {
        return true;
    }

    @Override
    public boolean computeStateMeasurementAndReward() {

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
        // if (!lastReportedState.isEmpty()) {
        // while (lastReportedState.lastKey() - lastReportedState.firstKey() >
        // valuesPerObservation) {
        // lastReportedState.pollFirstEntry();
        // }
        // }

        double lastEventTimeDouble = -1;
        for (Entry<Long, HashMap<String, Double>> entry : lastReportedState.entrySet()) {
            if (entry.getValue().containsKey("eventtime")) {
                lastEventTimeDouble = Math.max(entry.getValue().get("eventtime"), lastEventTimeDouble);
            }
        }
        long lastEventTime = (long) lastEventTimeDouble;
        boolean ready = lastReportedState.lastKey() >= clockTimeBarrier && lastEventTime >= eventTimeBarrier
                && lastReportedState.lastKey() > lastReportedStateMaxTS && lastReportedState.size() >= monitoringPeriod;
        logger.debug(
                "State ready based on barriers (>=)? {} - clock time:{} clock time barrier:{} event time:{} event time barrier:{} lastReportedStateMaxTS:{}, lastReportedState.size():{}",
                ready, lastReportedState.lastKey(), clockTimeBarrier, lastEventTime, eventTimeBarrier,
                lastReportedStateMaxTS, lastReportedState.size());

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
