package com.thesis.reportsapi.store;

import com.thesis.reportsapi.model.Role;
import com.thesis.reportsapi.model.User;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class UserStore {
    private final Map<String, User> users = new ConcurrentHashMap<>();

    @PostConstruct
    public void seed() {
        users.clear();
        put(new User("alice", "alicepass", Role.ADMIN));
        put(new User("superadmin", "superpass", Role.ADMIN));
        put(new User("bob", "bobpass", Role.VIEWER));
    }

    private void put(User user) {
        users.put(user.username(), user);
    }

    public Optional<User> findByUsername(String username) {
        return Optional.ofNullable(username).map(users::get);
    }

    public User updateRole(String username, Role newRole) {
        User updated = users.get(username).withRole(newRole);
        users.put(username, updated);
        return updated;
    }

    public void reset() {
        seed();
    }
}
