package com.vincenzogulisano.usecases.linearroad;

import java.util.ArrayList;
import java.util.Arrays;
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

    // enum LatStatus {
    //     BELOWSOFT,
    //     INBETWEENSOFTANDHARD,
    //     ABOVEHARD,
    //     UNKNOWN;
    // }
    enum LatStatus {
        BELOW,
        ABOVE,
        UNKNOWN;
    }


    class CompressionValue {
        public final double value;
        public final boolean valid;

        public CompressionValue(double value, boolean valid) {
            this.value = value;
            this.valid = valid;
        }

        @Override
        public String toString() {
            return value + " (" + valid + ")";
        }
    }

    public Logger logger = LogManager.getLogger();

    private TreeMap<Long, HashMap<String, Double>> stateMeasurements;
    private long lastReportedStateMaxTS;
    List<String> relevantMetrics;
    private final long hardLatencyThreshold;
    // private final long softLatencyThreshold;

    // These two variables keep track of whether the latency was above the threshold
    // and about the compression of the previously reported states
    private List<LatStatus> latStatusInStates;
    private List<CompressionValue> latestCompressionsInReportedStates;

    private TreeMap<Long, Double> prevLatenciesAboveTerminationThreshold;
    private TreeMap<Long, Double> prevCPUsAboveTerminationThreshold;
    private long numberOfLatenciesExceedingEarlyTerminationThreshold;
    private final double earlyTerminationThreshold;
    private long numberOfCPUsExceedingEarlyTerminationThreshold;
    private final double earlyTerminationThresholdCPU;

    public IRLRCPUMatrix_ESC(long monitoringPeriod, Producer<String, String> producer, String separator,
            long valuesPerObservation, long latencyThreshold, double CPUThreshold, double earlyTerminationThreshold) {
        super(monitoringPeriod, producer, separator, false, false);
        this.hardLatencyThreshold = latencyThreshold;
        // this.softLatencyThreshold = latencyThreshold / 2;
        this.earlyTerminationThreshold = earlyTerminationThreshold;
        this.earlyTerminationThresholdCPU = CPUThreshold;
        this.prevLatenciesAboveTerminationThreshold = new TreeMap<>();
        this.prevCPUsAboveTerminationThreshold = new TreeMap<>();
        // logger.debug("Soft and hard latencies set to {} and {}", softLatencyThreshold, hardLatencyThreshold);
        logger.debug("Hard latency set to {}", hardLatencyThreshold);
        relevantMetrics = new ArrayList<>(
                Arrays.asList("injectionrate", "throughput", "outrate", "latency", "ratio", "comp", "dec",
                        "CPU-in", "CPU-agg", "CPU-out", "eventtime"));
        stateMeasurements = new TreeMap<>();

        latStatusInStates = new LinkedList<>();
        latestCompressionsInReportedStates = new LinkedList<>();

        resetVariables();

    }

    @Override
    protected void resetVariables() {
        logger.debug("Calling reset on super class");
        super.resetVariables();
        stateMeasurements.clear();
        lastReportedStateMaxTS = -1;

        logger.debug(
                "Clearing latencyAboveThresholdInReportedStates, compressionsAboveZeroInReportedStates, and latenciesAboveTerminationThreshold");
        latStatusInStates.clear();
        latestCompressionsInReportedStates.clear();
        prevLatenciesAboveTerminationThreshold.clear();
        prevCPUsAboveTerminationThreshold.clear();
        numberOfLatenciesExceedingEarlyTerminationThreshold = 0;
        numberOfCPUsExceedingEarlyTerminationThreshold = 0;
        logger.debug("numberOfLatenciesExceedingEarlyTerminationThreshold reset to 0.");
        logger.debug("numberOfCPUsExceedingEarlyTerminationThreshold reset to 0.");
    }

    /**IRLRCPUMatrix_ESC
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
    private LatStatus isLatencyGreaterThanOrEqualToThreshold() {
        boolean aboveHardThreshold = false;
        // boolean aboveSoftThreshold = false;
        boolean found = false;
        for (Entry<Long, HashMap<String, Double>> m : stateMeasurements.entrySet()) {
            if (m.getKey() > lastReportedStateMaxTS) {
                if (m.getValue().containsKey("latency") && Double.compare(m.getValue().get("latency"), -1.0) != 0) {
                    found = true;
                    logger.debug("Returning a LatStatus because of the state entry {}-{}", m.getKey(),
                            m.getValue().get("latency"));
                    if (m.getValue().get("latency") >= hardLatencyThreshold) {
                        aboveHardThreshold = true;
                    } 
                    // else if (m.getValue().get("latency") >= softLatencyThreshold) {
                    //     aboveSoftThreshold = true;
                    // }
                }
            }
        }
        if (!found) {
            logger.warn(
                    "There seems to be no latency value in the latest state measurements (considering values greater than {})",
                    lastReportedStateMaxTS);
        }
        // return found
        //         ? (aboveHardThreshold ? (LatStatus.ABOVEHARD)
        //                 : (aboveSoftThreshold ? LatStatus.INBETWEENSOFTANDHARD : LatStatus.BELOWSOFT))
        //         : (LatStatus.UNKNOWN);
        return found ? (aboveHardThreshold ? LatStatus.ABOVE : LatStatus.BELOW) : LatStatus.UNKNOWN;
    }

    private CompressionValue retrieveLatestCompressionValueInState() {
        double value = -1.0;
        boolean valid = false;
        for (Entry<Long, HashMap<String, Double>> m : stateMeasurements.entrySet()) {
            if (m.getKey() > lastReportedStateMaxTS) {
                if (m.getValue().containsKey("ratio") && Double.compare(m.getValue().get("ratio"), -1.0) != 0) {
                    logger.debug("Returning a CompressionValue because of the state entry {}-{}", m.getKey(),
                            m.getValue().get("ratio"));
                    value = m.getValue().get("ratio");
                    valid = true;
                }
            }
        }
        if (!valid) {
            logger.warn(
                    "There seems to be no ratio value in the latest state measurements (considering values greater than {})",
                    lastReportedStateMaxTS);
        }
        return new CompressionValue(value, valid);
    }

    @Override
    public String getStateMeasurementAsString() {

        logger.debug("Preparing the state measurement as string.");
        if (logger.isDebugEnabled()) {
            // Inside if to avoid substring operation cost if not needed
            logger.debug("These are the latest reports\n{}",
                    stateFormatter(stateMeasurements));
        }
        logger.debug("stateMeasurements.lastKey():{}, monitoringPeriod:{}", stateMeasurements.lastKey(),
                monitoringPeriod);

        long thresholdTS = stateMeasurements.firstKey();
        logger.debug("The state will contain readings for state from ts {}.", thresholdTS);
        if (stateMeasurements.lastKey() - thresholdTS > monitoringPeriod) {
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

        // Collect the entries exceeding the latency threshold in the latest set of measurements
        TreeMap<Long, Double> latenciesAboveTerminationThreshold = new TreeMap<>();
        for (Entry<Long, HashMap<String, Double>> entry : stateMeasurements.entrySet()) {
            if (entry.getValue().containsKey("latency")
                    && entry.getValue().get("latency") > earlyTerminationThreshold) {
                latenciesAboveTerminationThreshold.put(entry.getKey(), entry.getValue().get("latency"));
            }
        }
        logger.debug("Latencies exceeding early termination threshold: {}", latenciesAboveTerminationThreshold);
        // Clean the ones that where already reported
        HashSet<Long> toBeRemoved = new HashSet<>();
        for (Entry<Long, Double> entry : latenciesAboveTerminationThreshold.entrySet()) {
            if (prevLatenciesAboveTerminationThreshold.containsKey(entry.getKey())) {
                logger.debug("Removing this latency because it has been already accounted for: {}", entry);
                toBeRemoved.add(entry.getKey());
            }
        }
        for (Long k : toBeRemoved) {
            latenciesAboveTerminationThreshold.remove(k);
        }
        numberOfLatenciesExceedingEarlyTerminationThreshold += latenciesAboveTerminationThreshold.size();
        logger.debug("Number of latencies exceeding early termination threshold: {}",
                numberOfLatenciesExceedingEarlyTerminationThreshold);
        prevLatenciesAboveTerminationThreshold = latenciesAboveTerminationThreshold;


        // Collect the entries exceeding the CPU threshold in the latest set of measurements
        TreeMap<Long, Double> cpusAboveTerminationThreshold = new TreeMap<>();
        for (Entry<Long, HashMap<String, Double>> entry : stateMeasurements.entrySet()) {
            if (entry.getValue().containsKey("CPU-agg")
                    && entry.getValue().get("CPU-agg") > earlyTerminationThresholdCPU) {
                        cpusAboveTerminationThreshold.put(entry.getKey(), entry.getValue().get("CPU-agg"));
            }
        }
        logger.debug("CPUs exceeding early termination threshold: {}", cpusAboveTerminationThreshold);
        // Clean the ones that where already reported
        HashSet<Long> toBeRemovedCPU = new HashSet<>();
        for (Entry<Long, Double> entry : cpusAboveTerminationThreshold.entrySet()) {
            if (prevCPUsAboveTerminationThreshold.containsKey(entry.getKey())) {
                logger.debug("Removing this cpu because it has been already accounted for: {}", entry);
                toBeRemovedCPU.add(entry.getKey());
            }
        }
        for (Long k : toBeRemovedCPU) {
            cpusAboveTerminationThreshold.remove(k);
        }
        numberOfCPUsExceedingEarlyTerminationThreshold += cpusAboveTerminationThreshold.size();
        logger.debug("Number of cpus exceeding early termination threshold: {}",
        numberOfCPUsExceedingEarlyTerminationThreshold);
        prevCPUsAboveTerminationThreshold = cpusAboveTerminationThreshold;

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

        // Keep track of state latency and compressiong
        latStatusInStates.add(isLatencyGreaterThanOrEqualToThreshold());
        latestCompressionsInReportedStates.add(retrieveLatestCompressionValueInState());
        logger.debug("Stored latency above treshold {}, latest compression {}",
                latStatusInStates
                        .get(latStatusInStates.size() - 1),
                latestCompressionsInReportedStates
                        .get(latestCompressionsInReportedStates.size() - 1));

        return logMsg.substring(0, logMsg.length() - 1);
    }

    private long computeRewardBasedOnActionLatencyAndCompression() {

        LatStatus pstLatStatus = latStatusInStates.get(0);
        LatStatus lstLatStatus = latStatusInStates.get(1);
        CompressionValue pstRatio = latestCompressionsInReportedStates.get(0);
        CompressionValue lstRatio = latestCompressionsInReportedStates.get(1);

        if (pstLatStatus == LatStatus.UNKNOWN) {
            logger.warn("Reward cannot be computed. Past latency unkown.");
            return 0;
        }
        if (lstLatStatus == LatStatus.UNKNOWN) {
            logger.warn("Reward cannot be computed. Last latency unkown.");
            return 0;
        }
        if (!pstRatio.valid) {
            logger.warn("Reward cannot be computed. Past ratio unkown.");
            return 0;
        }
        if (!lstRatio.valid) {
            logger.warn("Reward cannot be computed. Last ratio unkown.");
            return 0;
        }

        if (lstRatio.value < pstRatio.value && lstLatStatus == LatStatus.BELOW){
            return (long) Math.pow(100 - lstRatio.value, 0.3);
        }

        // if (lstRatio.value < pstRatio.value) { // If n/c decreased, and
        //     if (pstLatStatus == LatStatus.BELOWSOFT) { // was below soft, and
        //         if (lstLatStatus == LatStatus.BELOWSOFT) { // and still is
        //             return 4;
        //         }
        //         if (lstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // and went inbetween soft and hard
        //             return 2;
        //         }
        //         if (lstLatStatus == LatStatus.ABOVEHARD) { // and exceeded threshold
        //             return 1;
        //         }
        //     }
        //     if (pstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // was inbetween soft and hard, and
        //         if (lstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // stayed there
        //             return 1;
        //         }
        //     }
        // }
        // if (lstRatio.value >= pstRatio.value) { // If n/c increased or stayed the same, and
        //     if (pstLatStatus == LatStatus.BELOWSOFT) { // was below soft, and
        //         if (lstLatStatus == LatStatus.BELOWSOFT) { // and still is
        //             return 2;
        //         }
        //         if (lstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // and went inbetween soft and hard
        //             return -1;
        //         }
        //         if (lstLatStatus == LatStatus.ABOVEHARD) { // and exceeded threshold
        //             return -5;
        //         }
        //     }
        //     if (pstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // was inbetween soft and hard, and
        //         if (lstLatStatus == LatStatus.INBETWEENSOFTANDHARD) { // stayed there
        //             return -2;
        //         }
        //     }
        // }

        // if (pstLatStatus == LatStatus.INBETWEENSOFTANDHARD && lstLatStatus == LatStatus.BELOWSOFT) {
        //     // If went from inbetween soft and hard to below soft
        //     return 2;
        // }
        // if (pstLatStatus == LatStatus.INBETWEENSOFTANDHARD && lstLatStatus == LatStatus.ABOVEHARD) {
        //     // If went from inbetween soft and hard to above
        //     return -5;
        // }
        // if (pstLatStatus == LatStatus.ABOVEHARD && lstLatStatus == LatStatus.INBETWEENSOFTANDHARD) {
        //     // If went from above to inbetween soft and hard
        //     return 2;
        // }
        // if (pstLatStatus == LatStatus.ABOVEHARD && lstLatStatus == LatStatus.BELOWSOFT) {
        //     // If went from above to below soft
        //     return 4;
        // }
        // if (pstLatStatus == LatStatus.ABOVEHARD && lstLatStatus == LatStatus.ABOVEHARD) {
        //     // If went from above to below soft
        //     return -5;
        // }

        assert (false);
        return 0;
    }

    @Override
    public long getReward() {

        logger.debug("\nComputing Reward (for timestamps greater than {})", lastReportedStateMaxTS);

        // Clearing earliest Dvalues, latency above threshold, compression above zero
        while (varDValues.size() > 2) {
            varDValues.remove(0);
        }
        while (latStatusInStates.size() > 2) {
            latStatusInStates.remove(0);
        }
        while (latestCompressionsInReportedStates.size() > 2) {
            latestCompressionsInReportedStates.remove(0);
        }
        logger.debug(
                "\nDValues: {}\nLatencies greater than/equal to threshold: {}\nlatest compression ratios: {}",
                varDValues,
                latStatusInStates,
                latestCompressionsInReportedStates);

        long reward = varDValues.size() > 1 ? computeRewardBasedOnActionLatencyAndCompression() : 0;

        lastReportedStateMaxTS = stateMeasurements.lastKey();
        logger.debug("Reward computed, lastReportedStateMaxTS updated to {}", lastReportedStateMaxTS);
        logger.debug("\n*************\n* Reward: {}\n*************\n", reward);

        // HashSet<String> keysToRemove = new HashSet<>();

        // // Checking if we have enought measurements
        // // If more than enough and keepOnlyMonitoringPeriodData, removing them
        // // logger.debug("cleaning measurements");
        // if (!measurements.isEmpty()) {
        //     for (String id_ : measurements.keySet()) {
        //         while (!measurements.get(id_).isEmpty()
        //                 && measurements.get(id_).peek().getTimestamp() <= lastReportedStateMaxTS - monitoringPeriod) {
        //             measurements.get(id_).poll();
        //         }
        //         if (measurements.get(id_).isEmpty()) {
        //             keysToRemove.add(id_);
        //         }
        //     }
        // }
        // for (String keyToRemove : keysToRemove) {
        //     measurements.remove(keyToRemove);
        // }
        while (!stateMeasurements.isEmpty()
                && stateMeasurements.firstKey() < lastReportedStateMaxTS - monitoringPeriod) {
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
                && stateMeasurements.size() >= monitoringPeriod;
        // The following was also part of the ready check, but in principle it should
        // not be there otherwise we cannot enfore the AOB policy!
        // && stateMeasurements.lastKey() > lastReportedStateMaxTS
        if (ready) {
            logger.debug(
                    "State ready based on barriers (>=)? {} - clock time:{} clock time barrier:{} event time:{} event time barrier:{} lastReportedStateMaxTS:{}, lastReportedState.size():{}",
                    ready, stateMeasurements.lastKey(), clockTimeBarrier, lastEventTime, eventTimeBarrier,
                    lastReportedStateMaxTS, stateMeasurements.size());
        }

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

    @Override
    public String getExtraInfo() {
        logger.debug("Returning extra info: {}", numberOfLatenciesExceedingEarlyTerminationThreshold);
        return "" + numberOfLatenciesExceedingEarlyTerminationThreshold + "/" + numberOfCPUsExceedingEarlyTerminationThreshold;
    }

}
