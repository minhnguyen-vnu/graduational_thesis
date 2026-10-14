package com.thesis.reportsapi.dto;

import com.thesis.reportsapi.model.Role;

public record LoginResponse(String token, String username, Role role) {
}
