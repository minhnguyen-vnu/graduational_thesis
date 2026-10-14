package com.thesis.reportsapi.model;

public record Report(long id, String title, String owner, Classification classification) {
    public enum Classification {
        PUBLIC,
        CONFIDENTIAL
    }

    public Report withContent(String newTitle, Classification newClassification) {
        return new Report(id, newTitle, owner, newClassification);
    }
}
