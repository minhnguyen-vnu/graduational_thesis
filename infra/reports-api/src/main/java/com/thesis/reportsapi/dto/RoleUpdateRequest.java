package com.thesis.reportsapi.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

public record RoleUpdateRequest(
        @NotBlank @Schema(allowableValues = {"ADMIN", "VIEWER"}) String role) {
}
