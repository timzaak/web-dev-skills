# Spring Boot 后端模板

本模板用于 `/t-init` 生成 Java Spring Boot backend。替换占位符：

- `{{PROJECT_NAME}}`
- `{{PROJECT_NAME_PASCAL}}`
- `{{PROJECT_PACKAGE}}`
- `{{PROJECT_PACKAGE_PATH}}`

## 1. backend/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.9</version>
    <relativePath/>
  </parent>

  <groupId>{{PROJECT_PACKAGE}}</groupId>
  <artifactId>{{PROJECT_NAME}}</artifactId>
  <version>0.1.0</version>
  <name>{{PROJECT_NAME}}</name>

  <properties>
    <java.version>17</java.version>
    <springdoc.version>2.8.17</springdoc.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springdoc</groupId>
      <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
      <version>${springdoc.version}</version>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
```

## 2. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/{{PROJECT_NAME_PASCAL}}Application.java

```java
package {{PROJECT_PACKAGE}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {{PROJECT_NAME_PASCAL}}Application {

    public static void main(String[] args) {
        SpringApplication.run({{PROJECT_NAME_PASCAL}}Application.class, args);
    }
}
```

## 3. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/health/HealthService.java

```java
package {{PROJECT_PACKAGE}}.health;

import java.time.Instant;
import org.springframework.boot.actuate.health.HealthEndpoint;
import org.springframework.stereotype.Service;

@Service
public class HealthService {
    private final HealthEndpoint healthEndpoint;

    public HealthService(HealthEndpoint healthEndpoint) {
        this.healthEndpoint = healthEndpoint;
    }

    public HealthStatus currentStatus() {
        var health = healthEndpoint.health();
        return new HealthStatus("UP".equals(health.getStatus().getCode()), health.getStatus().getCode(), Instant.now());
    }
}
```

## 4. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/health/HealthStatus.java

```java
package {{PROJECT_PACKAGE}}.health;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;

@Schema(description = "Application health summary")
public record HealthStatus(
        boolean healthy,
        String status,
        Instant checkedAt
) {
}
```

## 5. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/web/HealthController.java

```java
package {{PROJECT_PACKAGE}}.web;

import {{PROJECT_PACKAGE}}.health.HealthService;
import {{PROJECT_PACKAGE}}.health.HealthStatus;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    private final HealthService healthService;

    public HealthController(HealthService healthService) {
        this.healthService = healthService;
    }

    @Operation(summary = "Health check")
    @ApiResponse(responseCode = "200", description = "Application health status")
    @GetMapping("/health")
    public HealthStatus health() {
        return healthService.currentStatus();
    }
}
```

## 6. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/web/ApiError.java

```java
package {{PROJECT_PACKAGE}}.web;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;

@Schema(description = "Stable API error response")
public record ApiError(
        String code,
        String message,
        Instant timestamp
) {
}
```

## 7. backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/web/ApiErrorHandler.java

```java
package {{PROJECT_PACKAGE}}.web;

import jakarta.validation.ConstraintViolationException;
import java.time.Instant;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiErrorHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiError> handleInvalidRequest(MethodArgumentNotValidException ex) {
        return ResponseEntity.badRequest()
                .body(new ApiError("VALIDATION_FAILED", "Request validation failed", Instant.now()));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    ResponseEntity<ApiError> handleConstraintViolation(ConstraintViolationException ex) {
        return ResponseEntity.badRequest()
                .body(new ApiError("VALIDATION_FAILED", "Request validation failed", Instant.now()));
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ApiError> handleUnexpected(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ApiError("INTERNAL_ERROR", "Unexpected server error", Instant.now()));
    }
}
```

## 8. backend/src/main/resources/application.yml

```yaml
spring:
  application:
    name: {{PROJECT_NAME}}

server:
  port: 8080

management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      probes:
        enabled: true

springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
```

## 9. backend/src/test/java/{{PROJECT_PACKAGE_PATH}}/{{PROJECT_NAME_PASCAL}}ApplicationTests.java

```java
package {{PROJECT_PACKAGE}};

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class {{PROJECT_NAME_PASCAL}}ApplicationTests {

    @Test
    void contextLoads() {
    }
}
```

## 10. backend/src/test/java/{{PROJECT_PACKAGE_PATH}}/web/HealthControllerTest.java

```java
package {{PROJECT_PACKAGE}}.web;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class HealthControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void returnsHealthStatus() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").exists());
    }
}
```

## 注意事项

- 默认 Java 版本为 17，这是 Spring Boot 3 的最低基线；如果目标环境明确使用 Java 21，可修改 `java.version` 并同步 README。
- 默认 OpenAPI 使用 springdoc，运行后访问 `/v3/api-docs` 和 `/swagger-ui.html`。
- `GET /health` 是给前端/demo 脚本的兼容入口；生产监控优先使用 Actuator `/actuator/health`。
- 新增业务模块时先遵循目标项目真实包结构，不强制套 `controller/service/repository` 目录。
