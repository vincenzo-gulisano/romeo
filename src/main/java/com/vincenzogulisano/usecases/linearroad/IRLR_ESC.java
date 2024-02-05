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
 * Notice this one overrides report and does not report based on a monitoring
 * period (that's why it passes -1 to the constructor of
 * EnvironmentStateCalculator). Not an elegant solution, could be done better
 * than passing around unused stuff
 */

public class IRLR_ESC extends EnvironmentStateCalculator {

    public Logger logger = LogManager.getLogger();

    private long IR; // Input Rate
    private long L; // Latency
    private double R; // Rate
    // private long ts;

    public IRLR_ESC(Producer<String, String> producer, String separator) {
        super(-1, producer, separator);
        resetVariables();
    }

    private void resetVariables() {
        IR = -1;
        L = -1;
        R = -1;
        // ts = -1;
    }

    @Override
    public void report(long ts, String id, double value) {

        this.lock.lock();

        if (resetRequest) {
            resetRequest = false;
            resetAcknowledged = true;
            resetCompleted = false;
            resetVariables();
            this.lock.unlock();
            return;
        }

        if (resetAcknowledged && !resetCompleted) {
            this.lock.unlock();
            return;
        }

        if (resetAcknowledged && resetCompleted) {
            resetAcknowledged = false;
            resetCompleted = false;
        }

        switch (id) {
            case "injectionrate":
                if (value > 0) {
                    IR = (long) value;
                    // this.ts = ts;
                }
                break;
            case "latency":
                if (value != -1) {
                    L = (long) value;
                    // this.ts = ts;
                }
                break;
            case "ratio":
                if (value != -1) {
                    R = value;
                    // this.ts = ts;
                }
                break;
            default:
                break;
        }

        if (IR != -1 && L != -1 && R != -1) {

            logger.debug("Checking if at least one token to send the state...");
            if (sendStateTokens.get() > 0) {
                logger.debug("One token is available");
                logger.debug("And state/reward too");
                sendStateTokens.set(0);

                String msg = getStateMeasurementAsString() + separator + getRewardAsString();
                logger.debug("Sending state/reward {}", msg);
                producer.send(new ProducerRecord<>("stats", msg));
                if (episodesLogger != null) {
                    episodesLogger.writeMeasurementEvent();
                }

            }

            resetVariables();

        }

        this.lock.unlock();
    }

    @Override
    public String getStateMeasurementAsString() {
        return String.format("%.2f,%.2f,%.2f", IR, L, R);
    }

    @Override
    public String getRewardAsString() {
        if (L > 1000) {
            return Long.toString((long) -(L - 1000) / 10);
        }
        return Long.toString((long) (100 - R));
    }

    @Override
    public boolean computeStateMeasurementAndReward() {
        throw new UnsupportedOperationException("Unimplemented method 'computeStateMeasurementAndReward'");
    }

}
