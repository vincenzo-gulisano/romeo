package com.vincenzogulisano.util;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

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
    private long lastMeasurementTime;
    private long lastTotalUptime;
    private boolean firstRetrieval;

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
                System.out.println("Found thread " + thread.getName() + " " + thread.getId());
                if (threadsToMonitor.contains(thread.getName())) {
                    System.out.println("... registered!");
                    threadNames.put(thread.getId(), thread.getName());
                }
            }

            for (TimeMetric stat : threadStats.values()) {
                stat.enable();
            }
            System.out.println("Starting cpu monitoring thread");
            threadMXBean = ManagementFactory.getThreadMXBean();
            Thread monitoringThread = new Thread(this::monitorThreadCPU);
            monitoringThread.start();
        } else {
            System.out.println("Monitoring is already started.");
        }
    }

    public void stopMonitoring() {
        isMonitoring = false;
        for (TimeMetric stat : threadStats.values()) {
            stat.disable();
        }
    }

    private void monitorThreadCPU() {
        while (isMonitoring) {

            long ts = System.currentTimeMillis();

            if (firstRetrieval) {
                firstRetrieval = false;

                // System.out.println("First CPU retrieval");

                lastTotalUptime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;

                // System.out.println("lastTotalUptime: " + lastTotalUptime);

                for (Map.Entry<Long, String> entry : threadNames.entrySet()) {

                    long threadId = entry.getKey();
                    String threadName = entry.getValue();
                    lastThreadCPUTime.put(threadName, threadMXBean.getThreadCpuTime(threadId));
                    // System.out
                    //         .println("lastThreadCPUTime for " + threadName + ": " + lastThreadCPUTime.get(threadName));

                }

            } else {

                long currentTotalUptime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;
                long totalUptimeDelta = currentTotalUptime - lastTotalUptime;
                lastTotalUptime = currentTotalUptime;

                // System.out.println("lastTotalUptime: " + lastTotalUptime);
                // System.out.println("totalUptimeDelta: " + totalUptimeDelta);

                for (Map.Entry<Long, String> entry : threadNames.entrySet()) {

                    long threadId = entry.getKey();
                    String threadName = entry.getValue();
                    long currentThreadCPUTime = threadMXBean.getThreadCpuTime(threadId);
                    long threadCPUDelta = currentThreadCPUTime - lastThreadCPUTime.get(threadName);
                    lastThreadCPUTime.put(threadName, currentThreadCPUTime);
                    // System.out
                    //         .println("lastThreadCPUTime for " + threadName + ": " + lastThreadCPUTime.get(threadName));
                    // System.out.println("delta ThreadCPUTime for " + threadName + ": " + threadCPUDelta);

                    double cpuUsage = (double) threadCPUDelta / (double) totalUptimeDelta * 100.0;
                    System.out.println(
                            String.format("%d - Thread ID %d Name %s CPU: %.2f", ts, threadId, threadName, cpuUsage));
                    this.threadStats.get(threadName).record(Math.round(cpuUsage));
                }

            }

            // long upTime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;
            // long temp = upTime - lastTotalUptime;
            // lastTotalUptime = upTime;
            // upTime = temp;

            // long measuringPeriod = System.currentTimeMillis();
            // temp = measuringPeriod - lastMeasurementTime;
            // lastMeasurementTime = measuringPeriod;
            // measuringPeriod = temp;

            // for (Map.Entry<Long, String> entry : threadNames.entrySet()) {

            // long threadId = entry.getKey();
            // String threadName = entry.getValue();
            // // ThreadInfo threadInfo = threadMXBean.getThreadInfo(threadId);
            // long cpuTime = threadMXBean.getThreadCpuTime(threadId);
            // long cpuTimeDelta = 0;

            // if (!firstRetrieval) {
            // cpuTimeDelta = cpuTime - lastThreadCPUTime.get(threadName);
            // double cpuUsage = cpuTimeDelta / upTime * 100;
            // System.out.println("Thread ID " + threadId + ", Thread Name " +
            // threadName + ": " + cpuUsage + "% CPU usage");
            // this.threadStats.get(threadName).record((long) cpuUsage);
            // }

            // lastThreadCPUTime.put(threadName, cpuTime);

            // double cpuUsage = getThreadCpuUsage(threadId, firstRetrieval);

            // }

            // Sleep for 1 second (adjust as needed)
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

    }

    // private double getThreadCpuUsage(long threadId) {

    // ThreadInfo threadInfo = threadMXBean.getThreadInfo(threadId);
    // long cpuTime = threadMXBean.getThreadCpuTime(threadId);

    // threadMXBean.getThreadUserTime(threadId);

    // if (cpuTime != -1 && threadInfo != null) {
    // long upTime = ManagementFactory.getRuntimeMXBean().getUptime() * 1000000;
    // double cpuUsage = (double) cpuTime / upTime;
    // return cpuUsage * 100.0; // Convert from fraction to percentage
    // }

    // return 0.0;
    // }

    public HashMap<String, Consumer<Object[]>> setStatReporter(StatReporter reporter) {
        System.out.println("CPU Monitor - Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        for (String threadName : threadsToMonitor) {
            consumers.put("CPU-" + threadName,
                    x -> reporter.report((long) x[0], "CPU-" + threadName, ((Long) x[1]).doubleValue()));
        }
        return consumers;
    }

    public void createStatistics() {
        System.out.println("CPU Monitor - Creating statistics");
        for (String threadName : threadsToMonitor) {
            threadStats.put(threadName,
                    LiebreContext.userMetrics().newAverageTimeMetric("CPU-" + threadName, "average"));
        }
    }

}
