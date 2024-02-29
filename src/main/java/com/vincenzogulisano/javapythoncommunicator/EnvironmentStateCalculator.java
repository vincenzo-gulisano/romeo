package com.vincenzogulisano.javapythoncommunicator;

import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.util.EpisodesLogger;

public abstract class EnvironmentStateCalculator implements StatReporter {

    protected class Pair<T, U> {
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
    protected final Producer<String, String> producer;

    protected Map<String, LinkedList<Pair<Long, Double>>> measurements;

    protected volatile boolean resetRequest;
    protected volatile boolean resetAcknowledged;
    protected volatile boolean resetCompleted;

    public Logger logger = LogManager.getLogger();
    public EpisodesLogger episodesLogger;

    protected AtomicInteger sendStateTokens;
    protected long clockTimeBarrier;
    protected long eventTimeBarrier;
    protected final String separator;

    protected ReentrantLock lock;

    protected boolean resetAllMeasurementsAfterReport;

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer, String separator,
            boolean resetAllMeasurementsAfterReport) {
        this.monitoringPeriod = monitoringPeriod;
        this.producer = producer;
        this.measurements = new HashMap<>();
        this.resetRequest = false;
        this.resetAcknowledged = false;
        this.resetCompleted = true;
        this.separator = separator;
        this.sendStateTokens = new AtomicInteger();
        this.lock = new ReentrantLock();
        this.resetAllMeasurementsAfterReport = resetAllMeasurementsAfterReport;
    }

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer, String separator) {
        this(monitoringPeriod, producer, separator, true);
    }

    public void close() {
        this.lock.lock();
        this.producer.close();
        this.lock.unlock();
    }

    public void setResetRequest() {
        this.resetRequest = true;
        logger.debug("SPE asking for a reset. resetRequest:{}", resetRequest);
    }

    public boolean getResetAcknowledged() {
        logger.debug("SPE invoking getResetAcknowledged. resetAcknowledged:{}", resetAcknowledged);
        return resetAcknowledged;
    }

    public void setResetCompleted() {
        this.resetCompleted = true;
        resetVariables();
        logger.debug("reset completed set by SPE. resetCompleted={}", resetCompleted);
    }

    public void addSendStateToken(long clockTimeBarrier, long eventTimeBarrier) {
        if (this.sendStateTokens.get() != 0) {
            logger.fatal("Cannot add a state token if one is already defined!");
            throw new RuntimeException("Cannot add a state token if one is already defined!");
        }
        this.sendStateTokens.incrementAndGet();
        this.clockTimeBarrier = clockTimeBarrier;
        this.eventTimeBarrier = eventTimeBarrier;
        logger.debug("added send state token, current value is {}, clockTimeBarrier:{}, eventTimeBarrier:{}",
                sendStateTokens.get(), clockTimeBarrier, eventTimeBarrier);
    }

    protected boolean valueIsToBeRegistered(String id, double value) {
        if (id.equals("outrate") && value == 0) {
            return false;
        }
        if ((id.equals("latency") || id.equals("ratio")) && value == -1) {
            return false;
        }
        return true;
    }

    protected void resetVariables() {
        measurements.clear();
    }

    @Override
    public void report(long ts, String id, double value) {

        this.lock.lock();

        if (resetRequest) {
            // System.out.println("EnvironmentStateCalculator - got a reset request, stop
            // storing stats for now");
            resetRequest = false;
            resetCompleted = false;
            resetAcknowledged = true;
            logger.debug(
                    "EnvironmentStateCalculator - resetting. resetRequest:{}, resetAcknowledged:{}, resetCompleted:{}",
                    resetRequest, resetAcknowledged, resetCompleted);
            measurements.clear();
            this.lock.unlock();
            return;
        }

        if (resetAcknowledged && !resetCompleted) {
            logger.debug(
                    "EnvironmentStateCalculator - reset acknowledge, but not completed. Not storing stats. resetAcknowledged:{}, resetCompleted:{}",
                    resetAcknowledged, resetCompleted);
            this.lock.unlock();
            return;
        }

        if (resetAcknowledged && resetCompleted) {
            // System.out.println("EnvironmentStateCalculator - reset acknowledge and
            // completed. Storing stats");
            resetAcknowledged = false;
            resetCompleted = false;
            logger.debug("Setting resetAcknowledged and resetCompleted to false");
        }

        // System.out.println(String.format("Storing %d,%s,%.2f", ts, id, value));

        // Check if there's something older than the monitoring period. If that is the
        // case, remove old stuff, report, and empty
        boolean dataSpansAtLeastTheMonitoringPeriod = false;
        HashSet<String> keysToRemove = new HashSet<>();
        if (!measurements.isEmpty()) {
            for (String id_ : measurements.keySet()) {
                while (!measurements.get(id_).isEmpty()
                        && measurements.get(id_).peek().getTimestamp() < ts - monitoringPeriod) {
                    dataSpansAtLeastTheMonitoringPeriod = true;
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

        if (dataSpansAtLeastTheMonitoringPeriod) {

            logger.debug(
                    "Checking if state measurement is available and there is at least one token to send the state...");
            if (sendStateTokens.get() > 0) {
                logger.debug("One token is available");
                if (computeStateMeasurementAndReward()) {
                    logger.debug("And state/reward too");
                    sendStateTokens.set(0);

                    String msg = getStateMeasurementAsString() + separator + getRewardAsString();
                    logger.debug("Sending state/reward {}", msg);
                    producer.send(new ProducerRecord<>("stats", msg));
                    if (episodesLogger != null) {
                        episodesLogger.writeMeasurementEvent();
                    }
                }
            }

            if (resetAllMeasurementsAfterReport) {
                measurements.clear();
            }
            // System.out.println(String.format("Sending message %s", msg));
            // logger.debug(logMsg);

        }

        if (valueIsToBeRegistered(id, value)) {
            if (!measurements.containsKey(id)) {
                measurements.put(id, new LinkedList<>());
            }
            measurements.get(id).add(new Pair<Long, Double>(ts, value));
            logger.debug("Registering {},{},{}", ts, id, String.format("%.2f", value));
            // System.out.println(String.format("EnvironmentStateCalculator registering
            // (%d,%s,%.2f)", ts, id, value));
        }

        this.lock.unlock();
    }

    @Override
    public void registerLogger(EpisodesLogger logger) {
        this.episodesLogger = logger;
    }

    public abstract String getStateMeasurementAsString();

    /**
     * Called when measurements over the specified monitoring period are avaible,
     * for the specialized class to try to compute a state measurement a reward
     * 
     * @return True if a state measurement and a Reward are available
     */
    public abstract boolean computeStateMeasurementAndReward();

    public abstract String getRewardAsString();

}
