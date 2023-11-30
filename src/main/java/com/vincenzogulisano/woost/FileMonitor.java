package com.vincenzogulisano.woost;

import java.io.IOException;
import java.nio.file.*;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import com.vincenzogulisano.javapythoncommunicator.StatReporter;

public class FileMonitor {

    private final String fileName;
    private final String id;
    private StatReporter statReporter;

    public FileMonitor(String fileName, String id) {
        this.fileName = fileName;
        this.id = id;
    }

    public void setStatReporter(StatReporter statReporter) {
        this.statReporter = statReporter;
    }

    public void startMonitoring() {
        ScheduledExecutorService executorService = Executors.newSingleThreadScheduledExecutor();

        Path filePath = Paths.get(fileName);
        try {
            // Read the existing content of the file
            Files.lines(filePath).forEach(this::processLine);

            // Watch the file for changes
            WatchService watchService = FileSystems.getDefault().newWatchService();
            filePath.getParent().register(watchService, StandardWatchEventKinds.ENTRY_MODIFY);

            executorService.scheduleAtFixedRate(() -> checkForChanges(watchService), 0, 1, TimeUnit.SECONDS);

        } catch (IOException | ClosedWatchServiceException e) {
            e.printStackTrace();
        }

    }

    private void checkForChanges(WatchService watchService) {
        try {
            WatchKey key = watchService.poll();
            if (key != null) {
                for (WatchEvent<?> event : key.pollEvents()) {
                    if (event.kind() == StandardWatchEventKinds.ENTRY_MODIFY) {
                        Path filePath = (Path) event.context();
                        Files.lines(filePath).forEach(this::processLine);
                    }
                }
                key.reset();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void processLine(String line) {
        long ts = Long.valueOf(line.split(",")[0]);
        double value = Double.valueOf(line.split(",")[1]);
        statReporter.report(ts, id, value);
    }

}
