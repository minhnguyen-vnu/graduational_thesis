FROM python:3.11-alpine as builder
RUN apk --update add bash nano g++
COPY ./requirements.txt /vampi/requirements.txt
WORKDIR /vampi
RUN pip install -r requirements.txt

# Build a fresh container, copying across files & compiled parts
FROM python:3.11-alpine
COPY . /vampi
WORKDIR /vampi
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin
ENV vulnerable=1
# THESIS SEED: stock VAmPI ships a 60s TTL, which expires mid-triple and masks the bug under
# test (a 401 is INCONCLUSIVE, never a verdict -- §5.3). Raised to 1h, matching reports-api.
ENV tokentimetolive=3600
# THESIS SEED: 0 = VULNERABLE (trust the stale JWT role claim), 1 = FIXED (re-read role).
ENV statefulrolecheck=0

ENTRYPOINT ["python"]
CMD ["app.py"]
