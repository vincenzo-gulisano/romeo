package com.vincenzogulisano.javapythoncommunicator;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import java.util.Queue;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class EnvironmentStateCalculator implements StatReporter {

    private class Pair<T, U> {
        private final T timestamp;
        private final U value;

        public Pair(T timestamp, U value) {
            this.timestamp = timestamp;
            this.value = value;
        }

        public T getTimestamp() {
            return timestamp;
        }

        public U getValue() {
            return value;
        }

        public String toString() {
            return String.format("(%d,%.2f)", timestamp, value);
        }
    }

    private final long monitoringPeriod;
    private final Producer<String, String> producer;

    private Map<String, Queue<Pair<Long, Double>>> measurements;

    private volatile boolean resetRequest;
    private volatile boolean resetAcknowledged;
    private volatile boolean resetCompleted;

    public Logger logger = LogManager.getLogger();

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer) {
        this.monitoringPeriod = monitoringPeriod;
        this.producer = producer;
        this.measurements = new HashMap<>();
        this.resetRequest = false;
        this.resetAcknowledged = false;
        this.resetCompleted = true;
    }

    public void setResetRequest() {
        this.resetRequest = true;
    }

    public boolean getResetAcknowledged() {
        return resetAcknowledged;
    }

    public void setResetCompleted() {
        this.resetCompleted = true;
    }

    private boolean valueIsToBeRegistered(String id, double value) {
        if (id.equals("outrate") && value == 0) {
            return false;
        }
        if (id.equals("latency") && value == -1) {
            return false;
        }
        return true;
    }

    @Override
    public void report(long ts, String id, double value) {

        if (resetRequest) {
            // System.out.println("EnvironmentStateCalculator - got a reset request, stop storing stats for now");
            resetRequest = false;
            resetAcknowledged = true;
            resetCompleted = false;
            measurements.clear();
            return;
        }

        if (resetAcknowledged && !resetCompleted) {
            // System.out.println("EnvironmentStateCalculator - reset acknowledge, but not completed. Not storing stats");
            return;
        }

        if (resetAcknowledged && resetCompleted) {
            // System.out.println("EnvironmentStateCalculator - reset acknowledge and completed. Storing stats");
            resetAcknowledged = false;
            resetCompleted = false;
        }

        // System.out.println(String.format("Storing %d,%s,%.2f", ts, id, value));

        // Check if there's something older than the monitoring period. If that is the
        // case, remove old stuff, report, and empty
        boolean dataSpansAtLeastTheMonitoringPeriod = false;
        if (!measurements.isEmpty()) {
            for (String id_ : measurements.keySet()) {
                while (!measurements.get(id_).isEmpty()
                        && measurements.get(id_).peek().getTimestamp() <= ts - monitoringPeriod) {
                    dataSpansAtLeastTheMonitoringPeriod = true;
                    measurements.get(id_).poll();
                }
                if (measurements.get(id_).isEmpty()) {
                    measurements.remove(id_);
                }
            }
        }
        if (dataSpansAtLeastTheMonitoringPeriod) {
            String logMsg = String.format("\nreporting at time %d statistics:\n", ts);
            String msg = String.format("%d", ts);
            for (String id_ : measurements.keySet()) {
                double avg = 0.0;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    avg += v.getValue();
                }
                avg /= measurements.get(id_).size();
                logMsg += 
                        String.format("...%s whose average is %.2f, computed from %d values\n",
                                id_, avg, measurements.get(id_).size());
                msg += String.format(",%s,%.2f", id_, avg);
            }
            measurements.clear();
            // System.out.println(String.format("Sending message %s", msg));
            logger.debug(logMsg);
            producer.send(new ProducerRecord<>("stats", msg));

        }

        if (valueIsToBeRegistered(id, value)) {
            if (!measurements.containsKey(id)) {
                measurements.put(id, new LinkedList<>());
            }
            measurements.get(id).add(new Pair<Long, Double>(ts, value));
            // System.out.println(String.format("EnvironmentStateCalculator registering
            // (%d,%s,%.2f)", ts, id, value));
        }
    }

}
