package com.thesis.reportsapi.model;

public record User(String username, String password, Role role) {
    public User withRole(Role newRole) {
        return new User(username, password, newRole);
    }
}
