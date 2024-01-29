package com.vincenzogulisano.usecases.linearroad;

import java.util.LinkedList;
import java.util.Queue;

import org.apache.kafka.clients.producer.Producer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentStateCalculator;

public class LatencyAndRatioDeltaESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();
    private double latency;
    private LinkedList<Double> ratios;

    public LatencyAndRatioDeltaESC(long monitoringPeriod, Producer<String, String> producer, String separator) {
        super(monitoringPeriod, producer, separator);
        latency = -1;
        ratios = new LinkedList<>();
    }

    @Override
    public String getStateMeasurementAsString() {
        assert (latency != -1 && ratios.size() == 2);
        return String.format("%.2f,%.2f,%.2f", latency, ratios.get(0), ratios.get(1));
    }

    @Override
    public boolean computeStateMeasurementAndReward() {

        logger.debug("Checking if state measurement and reward are available");

        for (String id_ : measurements.keySet()) {
            if (id_.equals("latency") || id_.equals("ratio")) {
                double avg = 0.0;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    avg += v.getValue();
                }
                avg /= measurements.get(id_).size();
                switch (id_) {
                    case "latency":
                        latency = avg;
                        logger.debug(String.format("registered latency %.2f", latency));
                        break;
                    case "ratio":
                        ratios.add(avg);
                        logger.debug("registered ratio {}", ratios.getLast());
                        if (ratios.size() > 2) {
                            double popped = ratios.poll();
                            logger.debug(String.format("... and popped %.2f", popped));
                        }
                        break;
                    default:
                        break;
                }
            }
        }

        return latency != -1 && ratios.size() == 2;

    }

    @Override
    public String getRewardAsString() {
        if (latency > 1000) {
            return Long.toString((long) -(latency-1000));
        }
        return Long.toString((long) (100-ratios.get(1)));
        // if (latency >= 1000) {
        //     return "-100";
        // }
        // if (ratios.get(1) < ratios.get(0)) {
        //     return "10";
        // }
        // return "0";
    }

}
