package com.thesis.reportsapi.store;

import com.thesis.reportsapi.model.Report;
import com.thesis.reportsapi.model.Report.Classification;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentSkipListMap;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class ReportStore {
    private final Map<Long, Report> reports = new ConcurrentSkipListMap<>();
    private final AtomicLong sequence = new AtomicLong(1);

    @PostConstruct
    public void seed() {
        reports.clear();
        sequence.set(1);

        for (int i = 1; i <= 5; i++) {
            Classification classification = (i % 2 == 1) ? Classification.PUBLIC : Classification.CONFIDENTIAL;
            long id = sequence.getAndIncrement();
            reports.put(id, new Report(id, "Report " + i, "alice", classification));
        }

    }

    public List<Report> findAll() {
        return List.copyOf(reports.values());
    }

    public Optional<Report> findById(long id) {
        return Optional.ofNullable(reports.get(id));
    }

    public Report create(String title, String owner, Classification classification) {
        long id = sequence.getAndIncrement();
        Report report = new Report(id, title, owner, classification);
        reports.put(id, report);
        return report;
    }

    public Report update(long id, String title, Classification classification) {
        Report updated = reports.get(id).withContent(title, classification);
        reports.put(id, updated);
        return updated;
    }

    public void delete(long id) {
        reports.remove(id);
    }

    public void reset() {
        seed();
    }
}
