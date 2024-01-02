package com.vincenzogulisano.javapythoncommunicator;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import java.util.Queue;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;

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

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer) {
        this.monitoringPeriod = monitoringPeriod;
        this.producer = producer;
        this.measurements = new HashMap<>();
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

        // Check if there's something older than the monitoring period. If that is the
        // case, remove old stuff, report, and empty
        boolean beforeMonitoringPeriod = false;
        while (!measurements.isEmpty()) {
            for (String id_ : measurements.keySet()) {
                while (!measurements.get(id_).isEmpty()
                        && measurements.get(id_).peek().getTimestamp() <= ts - monitoringPeriod) {
                    beforeMonitoringPeriod = true;
                    measurements.get(id_).poll();
                }
                if (measurements.get(id_).isEmpty()) {
                    measurements.remove(id_);
                }
            }
        }
        if (beforeMonitoringPeriod) {
            for (String id_ : measurements.keySet()) {
                double avg = 0.0;
                for (Pair<Long, Double> v : measurements.get(id_)) {
                    avg += v.getValue();
                }
                avg /= measurements.get(id_).size();
                System.out.println(
                        String.format("reporting at time %d statistic %s whose average is %.2f, computed from %s", ts,
                                id_, avg, measurements.get(id_)));
                producer.send(new ProducerRecord<>("stats", String.format("%d,%s,%.2f", ts, id_, avg)));
            }
            measurements.clear();
        }

        if (valueIsToBeRegistered(id, value)) {
            if (!measurements.containsKey(id)) {
                measurements.put(id, new LinkedList<>());
            }
            measurements.get(id).add(new Pair<Long, Double>(ts, value));
        }
    }

}
