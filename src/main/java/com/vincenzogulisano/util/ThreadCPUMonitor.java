package com.vincenzogulisano.util;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.TimeMetric;
import query.LiebreContext;

public class ThreadCPUMonitor {

    private final Map<Long, String> threadNames;
    private Map<String, TimeMetric> threadStats;
    private final List<String> threadsToMonitor;
    private volatile boolean isMonitoring;
    private ThreadMXBean threadMXBean;

    private Map<String, Long> lastThreadCPUTime;
    private long lastTotalUptime;
    private boolean firstRetrieval;

    public Logger logger = LogManager.getLogger();

    public ThreadCPUMonitor(List<String> threadsToMonitor) {
        this.threadNames = new HashMap<>();
        this.threadStats = new HashMap<>();
        this.isMonitoring = false;
        this.threadsToMonitor = threadsToMonitor;
        this.lastThreadCPUTime = new HashMap<>();
        this.lastTotalUptime = 0;
        firstRetrieval = true;
    }

    public void startMonitoring() {
        if (!isMonitoring) {
            isMonitoring = true;

            for (Thread thread : Thread.getAllStackTraces().keySet()) {
                // System.out.println("Found thread " + thread.getName() + " " +
                // thread.getId());
                if (threadsToMonitor.contains(thread.getName())) {
                    // System.out.println("... registered!");
                    threadNames.put(thread.getId(), thread.getName());
                }
            }

            for (TimeMetric stat : threadStats.values()) {
                stat.enable();
            }
            // System.out.println("Starting cpu monitoring thread");
            threadMXBean = ManagementFactory.getThreadMXBean();
            Thread monitoringThread = new Thread(this::monitorThreadCPU);
            monitoringThread.start();
        } else {
            // System.out.println("Monitoring is already started.");
        }
    }

    public void stopMonitoring() {
        isMonitoring = false;
    }

    private void monitorThreadCPU() {
        while (isMonitoring) {

            long ts = System.currentTimeMillis();

            if (firstRetrieval) {
                firstRetrieval = false;

                lastTotalUptime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;

                for (Map.Entry<Long, String> entry : threadNames.entrySet()) {

                    long threadId = entry.getKey();
                    String threadName = entry.getValue();
                    lastThreadCPUTime.put(threadName, threadMXBean.getThreadCpuTime(threadId));

                }

            } else {

                long currentTotalUptime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;
                long totalUptimeDelta = currentTotalUptime - lastTotalUptime;
                lastTotalUptime = currentTotalUptime;

                for (Map.Entry<Long, String> entry : threadNames.entrySet()) {

                    long threadId = entry.getKey();
                    String threadName = entry.getValue();
                    long currentThreadCPUTime = threadMXBean.getThreadCpuTime(threadId);
                    long threadCPUDelta = currentThreadCPUTime - lastThreadCPUTime.get(threadName);
                    lastThreadCPUTime.put(threadName, currentThreadCPUTime);

                    double cpuUsage = (double) threadCPUDelta / (double) totalUptimeDelta * 100.0;
                    // System.out.println(
                    // String.format("%d - Thread ID %d Name %s CPU: %.2f", ts, threadId,
                    // threadName, cpuUsage));
                    this.threadStats.get(threadName).record(Math.round(cpuUsage));
                }

            }

            // Sleep for 1 second (adjust as needed)
            try {
                Thread.sleep(250);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }

            // Pinging just in case
            for (TimeMetric metric : threadStats.values()) {
                metric.ping();
            }
        }

        for (TimeMetric stat : threadStats.values()) {
            stat.disable();
        }

    }

    public HashMap<String, Consumer<Object[]>> setStatReporter(StatReporter reporter) {
        logger.debug("CPU Monitor - Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        for (String threadName : threadsToMonitor) {
            consumers.put("CPU-" + threadName,
                    x -> reporter.report((long) x[0], "CPU-" + threadName, ((Long) x[1]).doubleValue()));
        }
        return consumers;
    }

    public void createStatistics() {
        logger.debug("CPU Monitor - Creating statistics");
        for (String threadName : threadsToMonitor) {
            threadStats.put(threadName,
                    LiebreContext.userMetrics().newAverageTimeMetric("CPU-" + threadName, "average"));
        }
    }

}
