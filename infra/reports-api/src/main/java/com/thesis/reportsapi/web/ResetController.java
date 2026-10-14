package com.thesis.reportsapi.web;

import com.thesis.reportsapi.store.ReportStore;
import com.thesis.reportsapi.store.UserStore;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class ResetController {
    private final UserStore userStore;
    private final ReportStore reportStore;

    public ResetController(UserStore userStore, ReportStore reportStore) {
        this.userStore = userStore;
        this.reportStore = reportStore;
    }

    @PostMapping("/reset")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "state reseeded")
    })
    public Map<String, String> reset() {
        userStore.reset();
        reportStore.reset();
        return Map.of("status", "reset");
    }
}
