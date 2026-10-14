# WFD — 36 spec, một spec một SUT

Nguồn: `infra/analysis/corpus/wfd/openapi-swagger/`, thư mục WFD tự gom một file một SUT.
Thay cho `wfd-inventory.md`, vốn quét cả cây nguồn nên lẫn 63 fixture test của microcks.
File YAML đọc bằng `ruby -ryaml` vì máy không có PyYAML.

Cột `ghi` đếm số operation POST, PUT, PATCH, DELETE. `CLAUDE.md` §6 chỉ gán nhãn operation ghi.

| # | Spec | Phiên bản | Đường dẫn | Ghi | Bytes |
|---|---|---|---|---|---|
| 1 | `webgoat.json` | 3.0.1 | 144 | 138 | 142109 |
| 2 | `familie-ba-sak.json` | 3.0.1 | 169 | 117 | 364750 |
| 3 | `ocvn.json` | 2.0 | 96 | 96 | 1335457 |
| 4 | `ohsome-api.json` | 2.0 | 67 | 67 | 565591 |
| 5 | `proxyprint.json` | 2.0 | 79 | 58 | 134886 |
| 6 | `tiltaksgjennomforing.json` | 3.0.1 | 75 | 55 | 112646 |
| 7 | `tracking-system.json` | 2.0 | 47 | 40 | 73472 |
| 8 | `microcks.json` | 3.0.1 | 64 | 37 | 111683 |
| 9 | `blogapi.json` | 3.0.0 | 30 | 29 | 79803 |
| 10 | `scout-api.json` | 2.0 | 21 | 28 | 52607 |
| 11 | `user-management.json` | 2.0 | 11 | 14 | 27006 |
| 12 | `features-service.json` | 2.0 | 11 | 12 | 14927 |
| 13 | `spring-ecommerce.json` | 2.0 | 21 | 12 | 37552 |
| 14 | `swagger-petstore.json` | 3.0.4 | 13 | 11 | 32797 |
| 15 | `genome-nexus.json` | 2.0 | 21 | 10 | 90941 |
| 16 | `gestaohospital.json` | 2.0 | 13 | 10 | 26906 |
| 17 | `pay-publicapi.json` | 3.0.1 | 13 | 7 | 108166 |
| 18 | `person-controller.json` | 3.0.1 | 6 | 7 | 73697 |
| 19 | `spring-rest-example.json` | 3.0.1 | 5 | 7 | 9045 |
| 20 | `catwatch.json` | 2.0 | 17 | 6 | 42859 |
| 21 | `market.json` | 2.0 | 10 | 6 | 21452 |
| 22 | `cwa-verification.json` | 3.0.1 | 5 | 5 | 10669 |
| 23 | `erc20-rest-service.json` | 2.0 | 13 | 5 | 18820 |
| 24 | `reservations-api.json` | 3.0.1 | 5 | 5 | 9013 |
| 25 | `http-patch-spring.json` | 3.0.1 | 2 | 4 | 7619 |
| 26 | `rest-news.json` | 2.0 | 4 | 4 | 9425 |
| 27 | `session-service.json` | 2.0 | 5 | 4 | 13069 |
| 28 | `quartz-manager.json` | 3.0.1 | 9 | 3 | 10885 |
| 29 | `languagetool.json` | 2.0 | 2 | 1 | 14888 |
| 30 | `spring-batch-rest.json` | 3.0.1 | 4 | 1 | 8598 |
| 31 | `bibliothek.json` | 3.0.1 | 8 | 0 | 18354 |
| 32 | `rest-ncs.json` | 2.0 | 6 | 0 | 7962 |
| 33 | `rest-scs.json` | 2.0 | 11 | 0 | 12478 |
| 34 | `restcountries.yaml` | 3.0.0 | 22 | 0 | 8595 |
| 35 | `spring-actuator-demo.json` | 3.0.1 | 2 | 0 | 1569 |
| 36 | `youtube-mock.yaml` | 2.0 | 1 | 0 | 418299 |

## Tổng

36 spec đọc được, 0 không đọc được. 1032 đường dẫn, 799 operation ghi.

Spec không có operation ghi nào (6): `bibliothek.json`, `rest-ncs.json`, `rest-scs.json`, `restcountries.yaml`, `spring-actuator-demo.json`, `youtube-mock.yaml`
