package com.vincenzogulisano.javapythoncommunicator;

import java.time.Duration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.util.EpisodesLogger;

import common.util.Util;

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

    protected final long monitoringPeriod;
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
    // protected boolean keepOnlyMonitoringPeriodData;

    private boolean dataSpansAtLeastTheMonitoringPeriod;

    // The following list keeps track of the D values passed by the agent. It's
    // protected so classes extending this one can operate on it as they wish. The
    // maxVarDValues is used to limit the max number of values stored in the list
    // (in case the extending class does not use them at all).
    protected final int maxVarDValues = 1000;
    protected List<Long> varDValues;

    private boolean runInternalThread;
    private final int internalThreadPeriod = 100;

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer, String separator,
            boolean resetAllMeasurementsAfterReport, boolean keepOnlyMonitoringPeriodData) {
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
        // this.keepOnlyMonitoringPeriodData = keepOnlyMonitoringPeriodData;
        this.dataSpansAtLeastTheMonitoringPeriod = false;

        varDValues = new LinkedList<>();

        runInternalThread = true;

        try {

            Thread internalThread = new Thread(() -> sendStateAndRewardIfAvailable());
            // Set the thread as a daemon so it doesn't prevent the program from exiting
            internalThread.setDaemon(true);
            // Start the thread
            internalThread.start();

        } catch (Exception e) {
            System.out.println(e);
        }

    }

    public EnvironmentStateCalculator(long monitoringPeriod, Producer<String, String> producer, String separator) {
        this(monitoringPeriod, producer, separator, true, true);
    }

    public void close() {
        this.lock.lock();
        this.producer.close();
        runInternalThread = false;
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

    @Override
    public void addSendStateToken(long clockTimeBarrier, long eventTimeBarrier, long dValue) {
        if (this.sendStateTokens.get() != 0) {
            logger.fatal("Cannot add a state token if one is already defined!");
            throw new RuntimeException("Cannot add a state token if one is already defined!");
        }
        this.sendStateTokens.incrementAndGet();
        this.clockTimeBarrier = clockTimeBarrier;
        this.eventTimeBarrier = eventTimeBarrier;
        logger.debug("added send state token, current value is {}, clockTimeBarrier:{}, eventTimeBarrier:{}, D:{}",
                sendStateTokens.get(), clockTimeBarrier, eventTimeBarrier, dValue);

        logger.debug("Storing D value {}", dValue);
        varDValues.add(dValue);
        while (varDValues.size() > maxVarDValues) {
            logger.debug("Removing D value {}", varDValues.get(0));
            varDValues.remove(0);
        }
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
        logger.debug("Clearing varDValues");
        varDValues.clear();
        dataSpansAtLeastTheMonitoringPeriod = false;
    }

    @Override
    public void report(long ts, String id, double value) {

        this.lock.lock();

        if (resetRequest) {
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
            resetAcknowledged = false;
            resetCompleted = false;
            logger.debug("Setting resetAcknowledged and resetCompleted to false");
        }

        // dataSpansAtLeastTheMonitoringPeriod = false;

        // Checking if we have enought measurements
        // If more than enough and keepOnlyMonitoringPeriodData, removing them
        if (!measurements.isEmpty()) {
            for (String id_ : measurements.keySet()) {
                while (!measurements.get(id_).isEmpty()
                        && measurements.get(id_).peek().getTimestamp() <= ts - monitoringPeriod) {
                    if (!dataSpansAtLeastTheMonitoringPeriod) {
                        logger.debug("dataSpansAtLeastTheMonitoringPeriod to true thanks to stat {}, ts {}, and current ts {}", id_,  measurements.get(id_).peek().getTimestamp(),ts);
                    }
                    dataSpansAtLeastTheMonitoringPeriod = true;
                    break;
                }
            }
        }

        if (valueIsToBeRegistered(id, value)) {
            if (!measurements.containsKey(id)) {
                measurements.put(id, new LinkedList<>());
            }
            measurements.get(id).add(new Pair<Long, Double>(ts, value));
            // logger.debug("Registering {},{},{}", ts, id, String.format("%.2f", value));
        }

        this.lock.unlock();
    }

    private void sendStateAndRewardIfAvailable() {

        while (runInternalThread) {

            this.lock.lock();

            if (!dataSpansAtLeastTheMonitoringPeriod) {
                // logger.debug("Internal thread, data does not span monitoring period");
            } else if (!(sendStateTokens.get() > 0)) {
                // logger.debug("Internal thread, no send state tokens");
            } else if (!areRewardAndNewStateMeasurementAvailable()) {
                // logger.debug("Internal thread, rewards and state not available");
            } else {

                logger.debug(
                        "Internal thread, data spans monitoring period, one token is available and reward/state are ready...");

                sendStateTokens.set(0);

                String msg = getStateMeasurementAsString() + separator + getReward() + separator + getExtraInfo();
                logger.debug("Sending state/reward/extrainfo {}", msg);
                producer.send(new ProducerRecord<>("stats", msg));
                if (episodesLogger != null) {
                    episodesLogger.writeMeasurementEvent();
                }

                if (resetAllMeasurementsAfterReport) {
                    measurements.clear();
                    dataSpansAtLeastTheMonitoringPeriod = false;
                }

            }

            this.lock.unlock();

            Util.sleep(internalThreadPeriod);

        }

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
    public abstract boolean areRewardAndNewStateMeasurementAvailable();

    public abstract long getReward();

    public abstract String getExtraInfo();

}
