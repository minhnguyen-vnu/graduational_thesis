# --- build stage ---
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /workspace
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B clean package -DskipTests

# --- run stage ---
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /workspace/target/reports-api-*.jar app.jar
EXPOSE 8080
# Default run is VULNERABLE mode; override with -e APP_SECURITY_STATEFUL_ROLE_CHECK=true for PATCHED.
ENTRYPOINT ["java", "-jar", "app.jar"]
