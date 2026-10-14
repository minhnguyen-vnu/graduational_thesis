package com.thesis.reportsapi.dto;

import com.thesis.reportsapi.model.Report;
import com.thesis.reportsapi.model.Report.Classification;

public record ReportResponse(long id, String title, String owner, Classification classification) {
    public static ReportResponse from(Report report) {
        return new ReportResponse(report.id(), report.title(), report.owner(), report.classification());
    }
}
