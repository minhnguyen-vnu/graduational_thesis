package com.thesis.reportsapi.dto;

import com.thesis.reportsapi.model.Report.Classification;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record ReportRequest(@NotBlank String title, @NotNull Classification classification) {
}
