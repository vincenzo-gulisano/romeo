package com.vincenzogulisano.usecases.linearroad;

import java.util.HashSet;
import java.util.LinkedList;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

/**
 * This is the one that has been used for Exp3
 */

public class IRLRCPU_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    private long IR; // Input Rate
    private long L; // Latency
    private double R; // Rate
    private double CPU;
    // private long ts;

    public IRLRCPU_ESC(long monitoringPeriod, Producer<String, String> producer, String separator) {
        super(monitoringPeriod, producer, separator);
        resetVariables();
    }

    protected void resetVariables() {
        IR = -1;
        L = -1;
        R = -1;
        CPU = -1;
        // ts = -1;
    }

    @Override
    public String getStateMeasurementAsString() {
        return String.format("%.2f,%.2f,%.2f,%.2f", (double) IR, (double) L, (double) R, (double) CPU);
    }

    @Override
    public long getReward() {
        if (L > 1000) {
            return (long) -(L - 1000) / 10;
        }
        return (long) (100 - R);
    }

    @Override
    public boolean areRewardAndNewStateMeasurementAvailable() {

        logger.debug("Checking if state measurement and reward are available");

        for (String id_ : measurements.keySet()) {
            if (id_.equals("injectionrate") || id_.equals("ratio") || id_.equals("CPU-agg")) {
                double avg = 0.0;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    avg += v.getValue();
                }
                avg /= measurements.get(id_).size();
                switch (id_) {
                    case "injectionrate":
                        IR = (long) avg;
                        logger.debug(String.format("registered injectionrate {}", IR));
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
            }
        }

        return IR != -1 && L != -1 && R != -1 && CPU != -1;

    }

}
