1. Glossary

Frame - logical unit of information that client and server can exchange
PTS - presentation timestamp
DTS - decoding timestamp
AAC - advanced audio codec
NALU - network abstract layer unit
VPS - video parameter set (H265 video specific NALU)
SPS - sequence parameter set (H264/H265 video specific NALU)
PPS - picture parameter set (H264/H265 video specific NALU)
ADTS header - *Audio Data Transport Stream Header*

2. Frame format

Client and server exchanges information using frames. Frames can be different types
and data passed within a frame depends on its type. Generic frame format:

+---+---+---+---+---+---+---+---+---+---+---+---+---+
| LENGTH (64)   | ID(64)|   TYPE(8) |  PAYLOAD(VAR) |
+---+---+---+---+---+---+---+---+---+---+---+---+---+

Or a to-scale representation where every box is a byte:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+-- ...
| 0 : 1 : 2 : 3 : 4 : 5 : 6 : 7 | 8 : 9 : 10: 11: 12: 13: 14: 15| 16|
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+-- ...
|            LENGTH             |              ID               | T |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+-- ...

- LENGTH(64): Each frame starts with length field, 64 bit size that tells size of the frame in bytes
(including predefined fields, so if LENGTH is 100 bytes, then PAYLOAD length is
100 - 8 - 8 - 1 = 82 bytes).
- ID(64): 64 bit frame sequence number, every new frame MUST have a sequence ID greater than that of the previous frame within the same track.
          Track ID would be specified in each frame. If track ID is not specified it's 0 implicitly.
- TYPE(8): 1 byte representing type of the frame.

Predefined frame types:
- 0x0 - connect frame
- 0x1 - connect ack frame
- 0x2 - video frame
- 0x3 - audio frame
- 0x4 - end of stream frame
- 0x5 - error frame
- 0x6 - ping frame
- 0x7 - ping ack frame
- 0x8 - bandwidth feedback frame (deprecated)
- 0x9 - bandwidth feedback frame
- 0xA - bandwidth probe frame
- 0XB - bandwidth probe ack frame
- 0xC - stream dry frame
- 0xD - video with track frame
- 0xE - audio with track frame
- 0XF - receiver loss report frame
- 0X10 - receiver delay report frame
- 0x11 - end of stream dry frame
- 0x12 - client information report frame
- 0x13 - application specific data frame

2.1 Connect frame

+---+---+---+---+---+---+---+-----+---+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|  LENGTH (64)  |    ID(64) | 0x0 |  VERSION(8)| VIDEO TIMESCALE(16)   | AUDIO TIMESCALE(16)   | BROADCAST ID(64)  |  PAYLOAD  |
+---+---+---+---+---+---+---+-----+---+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

- VERSION: version of the protocol (initial version is 0x0).
- PAYLOAD: application and version specific data that can be used by server. OPTIONAL
- VIDEO TIMESCALE: timescale for all video frame timestamps on this connection. Recommended value 30000
- AUDIO TIMESCALE: timescale for all audio samples timestamps on this connection, recommended value same as audio sample rate, for example 44100
- BROADCAST ID: identifier of broadcast, when reconnect, client MUST use the same broadcast ID

This is used by a broadcaster client. It sends a connect frame to initiate broadcasting. The client can start sending other frames right after "connect frame" without waiting acknowledgement from the server.
If server doesn't support VERSION sent by the client, server sends error frame with code <UNSUPPORTED VERSION>

2.2 Connect ack frame

+---+---+---+---+---+---+---+---+-----+
|    LENGTH (64)    |    ID(64) | 0x1 |
+---+---+---+---+---+---+---+---+-----+

Server sends "connect ack" frame in response to "connect frame" indicating that server accepts "version" and ready to receive data.
If client doesn't receive "connect ack" frame from the server within X seconds, connection considered BAD, all new frames won't be sent and connection will be closed
(there is no hard requirement on when connection must be closed).

2.3 Video Frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x2 |  CODEC(8)  | PTS(64)   | DTS(64)   |  VIDEO DATA   |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+

- CODEC - specifies codec that was used to encode this frame.
- PTS - presentation timestamp in connection video timescale
- DTS - decoding timestamp in connection video timescale

Supported type of codecs:
- 0x1 - H264
- 0x2 - H265
...

"VIDEO DATA" - variable length field, that carries actual video frame data that is codec dependent

For h264/h265 codec, "VIDEO DATA" are 1 or more NALUs in AVCC format:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+ ...
|   NALU_LENGTH(64) | NALU DATA |   NALU_LENGTH(64) | NALU DATA |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+ ...

EVERY h264 video key-frame MUST start with SPS/PPS NALUs.
EVERY h265 video key-frame MUST start with VPS/SPS/PPS NALUs.
Binary concatenation of "video data" from consecutive video frames, without data loss MUST produce VALID h264/h265 bitstream.

This has been deprecated in favor of video with track frame.

2.4 Audio Frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x3 |  CODEC(8)  | TIMESTAMP(64) |   AUDIO DATA  |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+

- CODEC - specifies codec that was used to encode this frame.
- TIMESTAMP - timestamp of first audio sample in Audio Data

Supported type of codecs:
- 0x1 - AAC
...

"AUDIO DATA" - variable length field, that carries 1 or more audio frames that is codec dependent.

For AAC codec, "AUDIO DATA" are 1 or more AAC samples, prefixed with TIMESTAMP and ADTS HEADER

152        158       ...     N
+---+---+---+---+---+---+---+...
| ADTS(56)  |  AAC SAMPLE   |
+---+---+---+---+---+---+---+...

Binary concatenation of all AAC samples in "audio data" from consecutive audio frames, without data loss MUST produce VALID AAC bitstream.

This has been deprecated in favor of audio with track frame.

2.5 End of stream frame

+---+---+---+---+----+---+---+
|    17     | ID(64) |  0x4  |
+---+---+---+---+----+---+---+

End of stream frame is sent by a broadcaster client when it's done sending data and is about to close the connection.
Server can ignore all frames sent after that.
There is no payload for this type of frame, so it's LENGTH always 17 bytes.

2.6 Error frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+----+-----+------+
|    LENGTH (64)    |    ID(64) | 0x5 |  SEQUENCE ID (64) | ERROR CODE (32) |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+----+-----+------+

- SEQUENCE ID - ID of the frame sent by the client that error is generated for, ID=0x0 indicates connection level error.
- ERROR CODE - 32 bit unsigned integer

Error frame can be sent by client or server to communicate that something is wrong.
Depending on error connection can be closed.

Error codes:
- <UNSUPPORTED VERSION>
- <UNSUPPORTED CODEC>
- <INVALID FRAME FORMAT>
- <CONNECTION REJECTED>

2.7 Ping frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x6 |  PAYLOAD(VAR)  |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+

- PAYLOAD: application and version specific data that can be used by server. OPTIONAL

Client send ping frame to server, and waiting for Ping ACK for the same sequence ID.
Client can have multiple ping message in the flight, and wait for each ACK to arrive.

2.8 Ping ack frame

+---+---+---+---+---+---+---+---+-----+----+---+---+-------+
|    LENGTH (64)    |    ID(64) | 0x7 |  ACK SEQUENCE ID (64) |
+---+---+---+---+---+---+---+---+-----+----+---+---+-------+

- ACK SEQUENCE ID - ID of the frame sent by the client that Ping Ack is generated for.

Server sends Ack frame in response to Ping frame indicating that the connection is alive.

2.9 Bandwidth feedback frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x8 | NUM MEASUREMENTS (32) | MEASUREMENTS (VAR)    |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+

MEASUREMENT:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+-..--+---+---+---+---+---+---+---+
| CLIENT START SEQUENCE ID (64)    |   CLIENT END SEQUENCE ID  (64)   |   BYTES (64)    | SERVER TS DELTA (32)  |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+-..--+---+---+---+---+---+---+---+

- NUM MEASUREMENTS - number of measurement sections to follow. Each measurement section is 64*3 bytes.
- CLIENT START SEQUENCE ID - ID of the frame sent by the client which begins the section of bandwidth measurement.
- CLIENT END SEQUENCE ID - ID of the frame sent by the client which ends the section of bandwidth measurement.
- BYTES - number of bytes received in range [Start Frame, End Frame], so including the Start Frame size.
- SERVER TIMESTAMP DELTA - time delta in milliseconds measured from the server from End Frame arrival time minus Start Frame arrival time.

Server sends Bandwidth feedback frame regularly with measurements of received data.
Client frame ids are sent back to the client so it can compare against its quiescence periods.

2.10 Bandwidth probe frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+
|    LENGTH (64)    |    ID(64) | 0xA |  PAYLOAD(VAR)  |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+

- PAYLOAD: random data generated by client, to measure bandwidth.

Client send bandwidth probe frame to server, and waiting for bandwidth probe ACK for the same sequence ID.
Client should only have one bandwidth probe message in the flight, and wait for it's ACK to arrive before sending another one.

2.11 Bandwidth probe ack frame

+---+---+---+---+---+---+---+---+-----+----+---+---+------+
|    LENGTH (64)    |    ID(64) | 0xB | ACK SEQUENCE ID (64) |
+---+---+---+---+---+---+---+---+-----+----+---+---+------+

- ACK SEQUENCE ID - ID of the frame sent by the client that Bandwidth probe Ack is generated for.

Server sends ack frame in response to Bandwidth probe frame, indicating that the full frame has been received.
Client can use it to measure bandwidth using the time between getting the ack and sending the bandwidth probe frame.

2.12 Stream dry frame

+---+---+---+---+---+---+---+---+-----+
|    LENGTH (64)    |    ID(64) | 0xC |
+---+---+---+---+---+---+---+---+-----+

Client sends stream dry frame to indicate the stream is interrupted.

2.13 Video with track frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0xD |  CODEC(8)  | PTS(64)   | DTS(64)   | TRACK ID(8)   |  REQUIRED FRAME OFFSET(16)    | VIDEO DATA    |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

- TRACK ID - ID of the track that this frame is on
- REQUIRED FRAME OFFSET - Distance from sequence ID of the frame that is required before this frame can be decoded.

This is the new video frame intended to deprecated the original video frame in 2.3, with additional fields to support track ID and required frame offset.

2.14 Audio with track frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0xE |  CODEC(8)  | TIMESTAMP(64) | TRACK ID(8)   |  AUDIO DATA   |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

- TRACK ID - ID of the track that this frame is on

This is the new audio frame intended to deprecated the original audio frame in 2.4, with an additional field to support track ID.

2.15 Receiver loss report frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0xF |  NUM REPORTS (8) | LOSS REPORTS PER TRACK (VAR)  |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+---+

LOSS REPORT PER TRACK:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
| TRACK ID (8)  |  NEXT SEQUENCE ID  (64)   |  NEWEST SEQUENCE ID (64)  | PACKETS EXPECTED (16) | PACKETS RECEIVED (16) |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

- NUM REPORTS - number of loss report per track sections to follow. Each report section is 21 bytes.
- NEXT SEQUENCE ID - ID of the frame in this track that the receiver expects next. Not necessary the same as (1 + newest ID) because packets may arrive out-of-order.
- NEWEST SEQUENCE ID - newest (largest) ID of the frame received so far in this track
- PACKETS EXPECTED - number of packets expected to receive since last sent report
- PACKETS RECEIVED - number of packets actually received since last sent report

Receiver sends the Receiver loss report frame regularly with loss information of the received data.

2.16 Receiver delay report frame

+---+---+---+---+---+---+---+---+------+----+---+---+---+---+--+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x10 |  NUM REPORTS (8)  |  DELAY REPORTS PER TRACK (VAR)   |
+---+---+---+---+---+---+---+---+------+----+---+---+---+---+--+---+---+---+---+---+---+---+---+

DELAY REPORT PER TRACK:

+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
| TRACK ID (8)  |   NUM ARRIVAL DATA (32)   |  ARRIVAL DATA PER FRAME (VAR) |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

ARRIVAL DATA PER FRAME:
+---+---+---+---+---+---+---+---+---+---+---+---+
| SEQUENCE ID (64)  |  RECEIVE TIMESTAMP (64)   |
+---+---+---+---+---+---+---+---+---+---+---+---+

- NUM REPORTS - number of delay report per track sections to follow
- TRACK ID - track ID for the following arrival data sections
- NUM ARRIVAL DATA - number of arrival data sections to follow. Each arrival data section is 16 bytes.
- SEQUENCE ID - ID of the frame that has the following data
- RECEIVE TIMESTAMP - receive timestamp of the specified frame

Receiver sends the Receiver delay report frame regularly with delay information of the received data.

2.17 End of stream dry frame

+---+---+---+---+---+---+---+---+-----+
|    LENGTH (64)    |    ID(64) | 0x11 |
+---+---+---+---+---+---+---+---+-----+

Client sends end of stream dry frame to indicate the stream's previous interruption is ended.

2.18 Client information frame

+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+---+---+---+---+---+---+---+
|    LENGTH (64)    |    ID(64) | 0x12 |  TIME SINCE PLAY SESSION START IN MS(32) | PAYLOAD IN JSON FORMAT (VAR)  |
+---+---+---+---+---+---+---+---+-----+----+---+---+---+---+--+---+---+---+---+---+---+---+---+---+---+---+---+---+

- TIME SINCE PLAY SESSION START IN MS - time elapsed since beginning of playback session, in ms.
- PAYLOAD IN JSON FORMAT - json containing relevant client information, such as time since last stall, time since last play, buffer size, max resolution supported or list of codecs supported.

Player sends the Client information report frame regularly to server to be used in ABR.

2.19 Application specific data frame

+---+---+---+---+---+---+---+---+------+---+---+---+---+---+--+---+---+---+---+---+--+
|    LENGTH (64)    |    ID(64) | 0x13 |  SUBTYPE(8)   |  PTS(64) |  PAYLOAD (VAR)   |
+---+---+---+---+---+---+---+---+------+---+---+---+---+---+--+---+---+---+---+---+--+

- SUBTYPE - enum identifying the application specific use case
- PTS - presentation timestamp in connection video timescale
- PAYLOAD - generic application specific data

Generic payload that contains application specific data with a subtype to identify the use case.

3. Assumptions/Requirements:

1. SEQUENCE ID starts with 1
2. SEQUENCE IDs can rollover.
3. SEQUENCE ID=N cannot be sent before SEQUENCE ID N-1 - sender must guarantee ordered sending within the same track.
4. Underlying transport protocol must guarantee 100% delivery in normal case, while in low latency scenario video/audio frames are allowed to be dropped.
5. Frame within the same track must be processed in ID order: N-1, N, N+1...
6. Connection keep-alive mechanism is up to underlying transport protocol
7. Audio timestamps and DTS are monotonically increasing between frames of the same type
8. Audio and video timestamps are synchronized.
9. If trackId is not specified, the frame is on track 0.

Notes:

Protocol supports changing audio and video codecs mid-broadcast. For video, client must
start with new key-frame when switching codecs and send codec specific parameters with new key-frame.

4. Quic Mapping

Quic mapping works differently in normal mode v.s. multi-stream mode. In normal mode, there is one single QUIC stream and every frame is in this stream. The following describes the more complicated multi-stream mode.

There should be 1 QUIC stream per frame/audio sample.   The first frame must be a Connect frame.  After that Video frames and Audio frames will follow using the following rules.

* Stream (audio or video) decode time X must be in a higher stream then any decode times before it.
* There currently is no cross stream synchronization of the streams.

Response Streams, Connect Ack and Error, will be in the response stream of the stream that sent it.

The mapping code from QUIC → Streaming protocol will handle out of order frames by waiting for the next stream for now.
