package com.thesis.reportsapi;

import com.thesis.reportsapi.dto.LoginRequest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpHeaders;

import java.util.Map;

final class TestSupport {
    private TestSupport() {
    }

    static String base(int port) {
        return "http://localhost:" + port;
    }

    @SuppressWarnings("unchecked")
    static String login(TestRestTemplate rt, int port, String username, String password) {
        Map<String, Object> body = rt.postForObject(
                base(port) + "/auth/login", new LoginRequest(username, password), Map.class);
        return (String) body.get("token");
    }

    static HttpHeaders bearer(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return headers;
    }
}
