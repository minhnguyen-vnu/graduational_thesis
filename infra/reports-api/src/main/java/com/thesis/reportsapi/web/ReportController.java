package com.thesis.reportsapi.web;

import com.thesis.reportsapi.dto.ErrorResponse;
import com.thesis.reportsapi.dto.ReportRequest;
import com.thesis.reportsapi.dto.ReportResponse;
import com.thesis.reportsapi.model.Report;
import com.thesis.reportsapi.security.ApiException;
import com.thesis.reportsapi.security.Authz;
import com.thesis.reportsapi.security.CurrentUser;
import com.thesis.reportsapi.store.ReportStore;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class ReportController {
    private final ReportStore reportStore;

    public ReportController(ReportStore reportStore) {
        this.reportStore = reportStore;
    }

    @GetMapping("/reports")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "all reports"),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public List<ReportResponse> list() {
        return reportStore.findAll().stream().map(ReportResponse::from).toList();
    }

    @GetMapping("/reports/{id}")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "the report"),
            @ApiResponse(responseCode = "400", description = "malformed id",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "404", description = "no such report",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public ReportResponse getOne(@PathVariable long id) {
        Report report = reportStore.findById(id)
                .orElseThrow(() -> new ApiException.NotFound("report not found"));
        return ReportResponse.from(report);
    }

    @PostMapping("/reports")
    @ResponseStatus(HttpStatus.CREATED)
    @ApiResponses({
            @ApiResponse(responseCode = "201", description = "report created"),
            @ApiResponse(responseCode = "400", description = "invalid request body",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "403", description = "admin role required",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public ReportResponse create(@Valid @RequestBody ReportRequest request, CurrentUser caller) {
        Authz.requireAdmin(caller);
        Report created = reportStore.create(request.title(), caller.username(), request.classification());
        return ReportResponse.from(created);
    }

    @PutMapping("/reports/{id}")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "report updated"),
            @ApiResponse(responseCode = "400", description = "invalid request body or malformed id",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "403", description = "admin role required",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "404", description = "no such report",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public ReportResponse update(@PathVariable long id, @Valid @RequestBody ReportRequest request,
                                 CurrentUser caller) {
        Authz.requireAdmin(caller);
        reportStore.findById(id).orElseThrow(() -> new ApiException.NotFound("report not found"));
        Report updated = reportStore.update(id, request.title(), request.classification());
        return ReportResponse.from(updated);
    }

    @DeleteMapping("/reports/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @ApiResponses({
            @ApiResponse(responseCode = "204", description = "report deleted"),
            @ApiResponse(responseCode = "400", description = "malformed id",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "403", description = "admin role required",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "404", description = "no such report",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public void delete(@PathVariable long id, CurrentUser caller) {
        Authz.requireAdmin(caller);
        reportStore.findById(id).orElseThrow(() -> new ApiException.NotFound("report not found"));
        reportStore.delete(id);
    }
}
