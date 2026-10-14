package com.thesis.reportsapi.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.thesis.reportsapi.dto.ErrorResponse;
import com.thesis.reportsapi.model.Role;
import com.thesis.reportsapi.model.User;
import com.thesis.reportsapi.store.UserStore;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;

@Component
public class AuthFilter extends OncePerRequestFilter {
    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtService jwtService;
    private final UserStore userStore;
    private final ObjectMapper objectMapper;
    private final boolean statefulRoleCheck;

    public AuthFilter(
            JwtService jwtService,
            UserStore userStore,
            ObjectMapper objectMapper,
            @Value("${app.security.stateful-role-check}") boolean statefulRoleCheck) {
        this.jwtService = jwtService;
        this.userStore = userStore;
        this.objectMapper = objectMapper;
        this.statefulRoleCheck = statefulRoleCheck;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return isPublic(request.getServletPath());
    }

    private boolean isPublic(String path) {
        return path.equals("/auth/login")
                || path.equals("/reset")
                || path.equals("/error")
                || path.startsWith("/v3/api-docs")
                || path.startsWith("/swagger-ui");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String header = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (header == null || !header.startsWith(BEARER_PREFIX)) {
            writeUnauthorized(response, "missing or malformed token");
            return;
        }

        String token = header.substring(BEARER_PREFIX.length()).trim();

        CurrentUser currentUser;
        try {
            currentUser = authenticate(token);
        } catch (JwtException | IllegalArgumentException ex) {
            writeUnauthorized(response, "invalid token");
            return;
        }

        request.setAttribute(CurrentUser.REQUEST_ATTRIBUTE, currentUser);
        chain.doFilter(request, response);
    }

    private CurrentUser authenticate(String token) {
        Claims claims = jwtService.parse(token);
        String username = claims.getSubject();

        Role effectiveRole;
        if (statefulRoleCheck) {
            Optional<User> user = userStore.findByUsername(username);
            if (user.isEmpty()) {
                throw new JwtException("subject no longer exists");
            }
            effectiveRole = user.get().role();
        } else {
            effectiveRole = Role.valueOf(claims.get("role", String.class));
        }
        return new CurrentUser(username, effectiveRole);
    }

    private void writeUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        objectMapper.writeValue(response.getWriter(), new ErrorResponse(message));
    }
}
