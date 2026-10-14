package com.thesis.reportsapi.security;

import com.thesis.reportsapi.model.Role;

public final class Authz {
    private Authz() {
    }

    public static void requireAdmin(CurrentUser caller) {
        if (caller.effectiveRole() != Role.ADMIN) {
            throw new ApiException.Forbidden("admin role required");
        }
    }
}
