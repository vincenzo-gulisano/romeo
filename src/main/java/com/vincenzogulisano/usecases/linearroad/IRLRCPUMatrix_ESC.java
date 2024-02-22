package com.vincenzogulisano.usecases.linearroad;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

/**
 * This is the one that has been used for Exp3
 */

public class IRLRCPUMatrix_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    private long IR; // Input Rate
    private long L; // Latency
    private double R; // Rate
    private double CPU;
    private long lastTS;
    // private long ts;

    private double[][] measurement;
    private long valuesPerObservation;

    public IRLRCPUMatrix_ESC(long monitoringPeriod, Producer<String, String> producer, String separator,
            long valuesPerObservation) {
        super(monitoringPeriod, producer, separator, false);
        this.valuesPerObservation = valuesPerObservation;
        resetVariables();

    }

    protected void resetVariables() {
        IR = -1;
        L = -1;
        R = -1;
        CPU = -1;
        lastTS = -1;
        // ts = -1;
    }

    @Override
    public String getStateMeasurementAsString() {
        String logMsg = "";
        for (int i = 0; i < measurement.length; i++) {
            for (int j = 0; j < measurement[i].length; j++) {
                logMsg += String.format("%.2f", measurement[i][j])
                        + (j < measurement[i].length - 1
                                || (j == measurement[i].length - 1 && i < measurement.length - 1) ? "," : "");
            }
        }
        // logger.debug("This is the resulting matrix\n{}", logMsg);
        return logMsg;
    }

    @Override
    public String getRewardAsString() {
        if (L > 1000) {
            return Long.toString((long) -(L - 1000) / 10);
        }
        return Long.toString((long) Math.round(Math.pow(100 - R, 1.5)));
    }

    @Override // In this case I am returning everything
    protected boolean valueIsToBeRegistered(String id, double value) {
        return true;
    }

    @Override
    public boolean computeStateMeasurementAndReward() {

        logger.debug("Checking if state measurement and reward are available");

        List<String> relevantMetrics = new ArrayList<>(Arrays.asList("injectionrate", "ratio", "CPU-agg", "latency"));

        logger.debug("Trying to find the min and max timestamps of the relevant metrics {}", relevantMetrics);
        long minTS = Long.MAX_VALUE;
        long maxTS = Long.MIN_VALUE;
        for (String metric : relevantMetrics) {
            if (measurements.containsKey(metric)) {
                logger.debug("Relevant measuremet: {}",measurements.get(metric));
                minTS = measurements.get(metric).getFirst().getTimestamp() < minTS
                        ? measurements.get(metric).getFirst().getTimestamp()
                        : minTS;
                maxTS = measurements.get(metric).getLast().getTimestamp() > maxTS
                        ? measurements.get(metric).getLast().getTimestamp()
                        : maxTS;
            }
        }
        if (minTS == Long.MAX_VALUE || maxTS == Long.MIN_VALUE) {
            logger.fatal("Trying to find the min and max timestamps of the relevant metrics {}", relevantMetrics);
            throw new RuntimeException("Could not find a single statistic for the relevant metrics " + relevantMetrics);
        }
        if (maxTS - minTS < valuesPerObservation - 1) {
            logger.debug("Cannot produce measurements, since I do not have {} values per observation",
                    valuesPerObservation);
            return false;
        }

        if (minTS <= maxTS - valuesPerObservation) {
            minTS = maxTS - valuesPerObservation + 1;
            logger.debug("There are more values than needed, changed minTS to {}", minTS);
        }

        logger.debug("MinTS={} MaxTS={}", minTS, maxTS);
        logger.debug("Creating a 2d matrix of {}x{} entries and populating it", relevantMetrics.size(),
                (int) (maxTS - minTS + 1));
        measurement = new double[relevantMetrics.size()][(int) (maxTS - minTS + 1)];
        for (int i = 0; i < measurement.length; i++) {
            for (int j = 0; j < measurement[i].length; j++) {
                measurement[i][j] = -1;
            }
        }
        for (int i = 0; i < relevantMetrics.size(); i++) {
            String metric = relevantMetrics.get(i);
            if (measurements.containsKey(metric)) {
                for (int j = 0; j < measurements.get(metric).size(); j++) {
                    if (measurements.get(metric).get(j).getTimestamp() >= minTS) {
                        measurement[i][(int) (measurements.get(metric).get(j).getTimestamp() - minTS)] = measurements
                                .get(metric).get(j).getValue();
                    }
                }
            }
        }

        for (String id_ : measurements.keySet()) {
            if (id_.equals("injectionrate") || id_.equals("ratio") || id_.equals("CPU-agg")) {
                double sum = 0.0;
                double count = 0.0;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    if (v.getValue() != -1) {
                        sum += v.getValue();
                        count++;
                    }
                }
                double avg = count > 0 ? sum / count : -1;
                switch (id_) {
                    case "injectionrate":
                        IR = (long) avg;
                        logger.debug("registered injectionrate {}", IR);
                        break;
                    case "ratio":
                        R = avg;
                        logger.debug("registered ratio {}", R);
                        break;
                    case "CPU-agg":
                        CPU = avg;
                        logger.debug("registered cpu {}", CPU);
                        break;
                    default:
                        break;
                }
            }
            if (id_.equals("latency")) {
                L = -1;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    L = (long) (v.getValue() > L ? v.getValue() : L);
                }
                logger.debug("registered latency {}", L);
            }
        }

        // Notice I set lastTS + 1 to make sure I send the state when all the
        // measurements for the same second have been received
        boolean ready = maxTS > lastTS && L != -1 && R != -1;
        logger.debug("maxTS {} / lastTS {} / maxTS > lastTS {} / L {} / R {}/ ready {}", maxTS, lastTS,
                maxTS > lastTS, L,
                R, ready);

        if (ready) {
            lastTS = maxTS;

            String logMsg = "";
            logMsg += "ts" + "\t";
            for (long j = minTS; j <= maxTS; j++) {
                logMsg += j + (j == maxTS ? "\n" : "\t");
            }
            for (int i = 0; i < relevantMetrics.size(); i++) {
                logMsg += relevantMetrics.get(i) + "\t";
                for (int j = 0; j < measurement[i].length; j++) {
                    logMsg += String.format("%.2f", measurement[i][j]) + (j == measurement[i].length - 1 ? "\n" : "\t");
                }
            }
            logger.debug("This is the resulting matrix\n{}", logMsg);

        }
        return ready;

    }

}
