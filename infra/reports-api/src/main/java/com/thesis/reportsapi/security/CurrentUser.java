package com.thesis.reportsapi.security;

import com.thesis.reportsapi.model.Role;

public record CurrentUser(String username, Role effectiveRole) {
    public static final String REQUEST_ATTRIBUTE = "com.thesis.reportsapi.currentUser";
}
