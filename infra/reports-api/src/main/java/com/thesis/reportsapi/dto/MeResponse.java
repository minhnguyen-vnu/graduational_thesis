package com.thesis.reportsapi.dto;

import com.thesis.reportsapi.model.Role;

public record MeResponse(String username, Role role) {
}
