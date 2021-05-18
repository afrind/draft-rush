---
title: "RUSH - Realtime Updated dynamic adaptive Streaming over HTTP"
abbrev: "rush"
docname: draft-frindell-rush-latest
category: info

ipr: trust200902
area: General
workgroup: TODO Working Group
keyword: Internet-Draft

stand_alone: yes
smart_quotes: no
pi: [toc, sortrefs, symrefs]

author:
 -
    ins: A. Frindell
    name: Alan Frindell
    organization: Facebook
    email: afrind@fb.com
 -
    ins: K. Pugin
    name: Kirill Pugin
    organization: Facebook
    email: ikir@fb.com
 -
    ins: J. Cenzano
    name: Jordi Cenzano
    organization: Facebook
    email: jcenzano@fb.com
 -
    ins: J. Weissman
    name: Jake Weissman
    organization: Facebook
    email: jakeweissman@fb.com

normative:
  RFC2119:

informative:



--- abstract

TODO Abstract

--- middle

# Introduction

TODO Introduction

# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in BCP 14 {{RFC2119}} {{!RFC8174}}
when, and only when, they appear in all capitals, as shown here.

Frame:

: logical unit of information that client and server can exchange

PTS:

: presentation timestamp


DTS:

: decoding timestamp

AAC:

: advanced audio codec

NALU:

: network abstract layer unit

VPS:

: video parameter set (H265 video specific NALU)

SPS:

: sequence parameter set (H264/H265 video specific NALU)

PPS:

: picture parameter set (H264/H265 video specific NALU)

ADTS header:

: *Audio Data Transport Stream Header*


# Theory of Operations

# Wire Format

## Frame Header

Client and server exchanges information using frames. Frames can be different
types and data passed within a frame depends on its type.

Generic frame format:

~~~
0       1       2       3       4       5       6       7
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
|Type(8)| Payload ...
+-------+------------------------------------------------------+
~~~

Length(64):
: Each frame starts with length field, 64 bit size that tells size of the frame
in bytes (including predefined fields, so if LENGTH is 100 bytes, then PAYLOAD
length is 100 - 8 - 8 - 1 = 82 bytes).

ID(64):
: 64 bit frame sequence number, every new frame MUST have a sequence ID greater
than that of the previous frame within the same track.  Track ID would be
specified in each frame. If track ID is not specified it's 0 implicitly.

Type(8):
: 1 byte representing type of the frame.

Predefined frame types:

| Frame Type | Frame |
|------------|-------|
| 0x0 | connect frame|
| 0x1 | connect ack frame |
| 0x2 | video frame |
| 0x3 | audio frame |
| 0x4 | end of stream frame |
| 0x5 | error frame |
| 0x6 | ping frame |
| 0x7 | ping ack frame |
| 0x8 | bandwidth feedback frame (deprecated) |
| 0x9 | bandwidth feedback frame |
| 0xA | bandwidth probe frame |
| 0XB | bandwidth probe ack frame |
| 0xC | stream dry frame |
| 0xD | video with track frame |
| 0xE | audio with track frame |
| 0XF | receiver loss report frame |
| 0X10 | receiver delay report frame |
| 0x11 | end of stream dry frame |
| 0x12 | client information report frame |
| 0x13 | application specific data frame |

## Frames

### Connect frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------+---------------+---------------+--------------+
| 0x0   |Version|Video Timescale|Audio Timescale|
+-------+-------+---------------+---------------+--------------+
|                    Broadcast ID(64)                          |
+--------------------------------------------------------------+
| Payload ...
+--------------------------------------------------------------+
~~~

Version:
: version of the protocol (initial version is 0x0).

Video Timescale:
: timescale for all video frame timestamps on this connection. Recommended value
30000

Audio Timescale:
: timescale for all audio samples timestamps on this connection, recommended
value same as audio sample rate, for example 44100

Broadcast ID:
: identifier of broadcast, when reconnect, client MUST use the same broadcast ID

Payload:
: application and version specific data that can be used by server. OPTIONAL

This is used by a broadcaster client. It sends a connect frame to initiate
broadcasting. The client can start sending other frames right after "Connect
frame" without waiting acknowledgement from the server.

If server doesn't support VERSION sent by the client, server sends error frame
with code `UNSUPPORTED VERSION`

### Connect Ack frame

~~~
0       1       2       3       4       5       6       7
+--------------------------------------------------------------+
|                          17                                  |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x1   |
+-------+
~~~

Server sends "Connect Ack" frame in response to "Connect" frame indicating that
server accepts "version" and ready to receive data.

If client doesn't receive "Connect Ack" frame from the server within X seconds,
connection considered BAD, all new frames won't be sent and connection will be
closed (there is no hard requirement on when connection must be closed).

### Video Frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------+----------------------------------------------+
| 0x2   | Codec |
+-------+-------+----------------------------------------------+
|                        PTS (64)                              |
+--------------------------------------------------------------+
|                        DTS (64)                              |
+--------------------------------------------------------------+
| Video Data ...
+--------------------------------------------------------------+
~~~

Codec:
: specifies codec that was used to encode this frame.

PTS:
: presentation timestamp in connection video timescale

DTS:
: decoding timestamp in connection video timescale

Supported type of codecs:

| Type | Codec |
|------|-------|
|0x1| H264|
|0x2| H265|


Video Data:
: variable length field, that carries actual video frame data that is codec
dependent

For h264/h265 codec, "Video Data" are 1 or more NALUs in AVCC format:

~~~
0       1       2       3       4       5       6       7
+--------------------------------------------------------------+
|                    NALU Length (64)                          |
+--------------------------------------------------------------+
|                    NALU Data ...
+--------------------------------------------------------------+
~~~

EVERY h264 video key-frame MUST start with SPS/PPS NALUs.
EVERY h265 video key-frame MUST start with VPS/SPS/PPS NALUs.

Binary concatenation of "video data" from consecutive video frames, without data loss MUST produce VALID h264/h265 bitstream.

NOTE: This has been deprecated in favor of Video with Track frame.

### Audio Frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x3   | Codec |
+-------+-------+----------------------------------------------+
|                      Timestamp (64)                          |
+--------------------------------------------------------------+
| Audio Data ...
+--------------------------------------------------------------+
~~~

Codec:
: specifies codec that was used to encode this frame.

Timestamp:
: timestamp of first audio sample in Audio Data.  TODO: describe format

Supported type of codecs:

| Type| Codec|
|-----|------|
|0x1| AAC|


Audio Data:
: variable length field, that carries 1 or more audio frames that is codec
dependent.

For AAC codec, "Audio Data" are 1 or more AAC samples, prefixed with TIMESTAMP
and ADTS HEADER

NOTE: The picture doesn't show a timestamp, is it embedded in ADTS?

~~~
152        158       ...     N
+---+---+---+---+---+---+---+...
| ADTS(56)  |  AAC SAMPLE   |
+---+---+---+---+---+---+---+...
~~~

Binary concatenation of all AAC samples in "Audio Data" from consecutive audio
frames, without data loss MUST produce VALID AAC bitstream.

This has been deprecated in favor of Audio with Track frame.

### End of Stream frame

~~~
+--------------------------------------------------------------+
|                          17                                  |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x4   |
+-------+
~~~

End of stream frame is sent by a broadcaster client when it's done sending data
and is about to close the connection.

Server can ignore all frames sent after that.  There is no payload for this type
of frame, so it's Length always 17 bytes.

### Error frame

~~~
+--------------------------------------------------------------+
|                       29                                     |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x5   |
+-------+------------------------------------------------------+
|                   Sequence ID (64)                           |
+------------------------------+-------------------------------+
|      Error Code (32)         |
+------------------------------+
~~~

Sequence ID:
: ID of the frame sent by the client that error is generated for, ID=0x0
indicates connection level error.

Error Code:
: 32 bit unsigned integer

Error frame can be sent by client or server to communicate that something is
wrong.

Depending on error connection can be closed.

Error codes

UNSUPPORTED VERSION:

UNSUPPORTED CODEC:

INVALID FRAME FORMAT:

CONNECTION REJECTED:

TODO: Describe, move to Error handling section?

### Ping frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x6   | Payload ...
+-------+------------------------------------------------------+
~~~

Payload:
: application and version specific data that can be used by server. OPTIONAL

Client send ping frame to server, and waiting for Ping ACK for the same sequence ID.

Client can have multiple ping message in the flight, and wait for each ACK to
arrive.

### Ping Ack frame

~~~
+--------------------------------------------------------------+
|                       25                                     |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x7   |
+-------+------------------------------------------------------+
|                Ack Sequence ID (64)                          |
+--------------------------------------------------------------+
~~~

Ack Sequence ID:
: ID of the frame sent by the client that Ping Ack is generated for.

Server sends Ack frame in response to Ping frame indicating that the connection
is alive.

### Bandwidth Feedback frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x8   |
+-------+----------------------+-------------------------------+
|   Num Measurements (32)      | Measurements ...
+------------------------------+-------------------------------+
~~~

Num Measurements:
: number of measurement sections to follow. Each measurement section is 64*3
bytes.

Measurement:

~~~
+--------------------------------------------------------------+
|                   Client Start Sequence ID (64)              |
+--------------------------------------------------------------+
|                   Client End Sequence ID (64)                |
+--------------------------------------------------------------+
|                   Bytes (64)                                 |
+------------------------------+-------------------------------+
|   Server TS Delta (32)       |
+------------------------------+
~~~

Client Start Sequence ID:
: ID of the frame sent by the client which begins the section of bandwidth
measurement.

Client End Sequence ID:
: ID of the frame sent by the client which ends the section of bandwidth
measurement.

Bytes:
: number of bytes received in range [Start Frame, End Frame], so including the
Start Frame size.

Server Timestamp Delta:
: time delta in milliseconds measured from the server from End Frame arrival
time minus Start Frame arrival time.

Server sends Bandwidth Feedback frame regularly with measurements of received
data.

Client frame ids are sent back to the client so it can compare against its
quiescence periods.

### Bandwidth Probe frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0xA   | Payload ...
+-------+------------------------------------------------------+
~~~

Payload:
: random data generated by client, to measure bandwidth.

Client send bandwidth probe frame to server, and waiting for bandwidth probe ACK
for the same sequence ID.

Client should only have one bandwidth probe message in the flight, and wait for
it's ACK to arrive before sending another one.

### Bandwidth Probe Ack frame

~~~
+--------------------------------------------------------------+
|                       17                                     |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0xB   |
+-------+
~~~

Ack Sequence ID:
: ID of the frame sent by the client that Bandwidth probe Ack is generated for.

Server sends ack frame in response to Bandwidth probe frame, indicating that the
full frame has been received.

Client can use it to measure bandwidth using the time between getting the ack
and sending the bandwidth probe frame.

### Stream Dry frame

~~~
+--------------------------------------------------------------+
|                       17                                     |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0xC   |
+-------+
~~~

Client sends stream dry frame to indicate the stream is interrupted.

### Video with Track frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------+----------------------------------------------+
| 0xD   | Codec |
+-------+-------+----------------------------------------------+
|                        PTS (64)                              |
+--------------------------------------------------------------+
|                        Track ID (64)                         |
+---------------+----------------------------------------------+
| Req Fr Offset | Video Data ...
+---------------+----------------------------------------------+
~~~

Track ID:
: ID of the track that this frame is on

Required Frame Offset:
: Distance from sequence ID of the frame that is required before this frame can
be decoded.

This is the new video frame intended to deprecate the original Video frame in
{{video-frame}}, with additional fields to support Track ID and Required Frame
Offset.

TODO: describe other fields, or just remove deprecated frame types.  This frame
also removed DTS?

### Audio with Track frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0xE   | Codec |
+-------+-------+----------------------------------------------+
|                      Timestamp (64)                          |
+-------+------------------------------------------------------+
|TrackID|
+-------+------------------------------------------------------+
| Audio Data ...
+--------------------------------------------------------------+
~~~

Track ID:
: ID of the track that this frame is on

This is the new audio frame intended to deprecated the original Audio frame in
{{audio-frame}}, with an additional field to support Track ID.

TODO: Remove old Audio frame description and merge other field descriptions here

### Receiver Loss Report frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0xF   |Reports| Loss Reports Per Track...
+-------+-------+----------------------------------------------+
~~~

Reports:
: number of loss report per track sections to follow. Each report section is 21
bytes.

Loss Report per Track:

~~~
+-------+
|TrackID|
+--------------------------------------------------------------+
|                    Next Sequence ID (64)                     |
+--------------------------------------------------------------+
|                    Newest Sequence ID (64)                   |
+--------------+---------------+-------------------------------+
|Pkts Expected | Pkts Received |
+--------------+---------------+
~~~

Next Sequence ID:
: ID of the frame in this track that the receiver expects next. Not necessary
the same as (1 + newest ID) because packets may arrive out-of-order.

Newest Sequence ID:
: newest (largest) ID of the frame received so far in this track

Packets Expected:
: number of packets expected to receive since last sent report

Packets Received:
: number of packets actually received since last sent report

Receiver sends the Receiver loss report frame regularly with loss information of
the received data.

### Receiver Delay Report frame


~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x10  |Reports| Delay Reports Per Track...
+-------+-------+----------------------------------------------+
~~~

Reports:
: number of delay report per track sections to follow

Delay Report per Track:

~~~
+-------+
|TrackID|
+-------------------------------+-------------------------------+
|  Num Arrival Data (32)        |   Arrival Data per Frame ...
+-------------------------------+-------------------------------+
~~~

Track ID:
: track ID for the following arrival data sections

Num Arrival Data:
: number of arrival data sections to follow. Each arrival data section is 16
bytes.

Arrival Data per Frame:

~~~
+--------------------------------------------------------------+
|                       Sequence ID (64)                       |
+--------------------------------------------------------------+
|                       Receive Timestamp (64)                 |
+-------+------------------------------------------------------+
~~~

Sequence ID:
: ID of the frame that has the following data

Receive Timestamp:
: receive timestamp of the specified frame

Receiver sends the Receiver delay report frame regularly with delay information
of the received data.

### End of Stream Dry frame

~~~
+--------------------------------------------------------------+
|                       17                                     |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+------------------------------------------------------+
| 0x11  |
+-------+
~~~

Client sends End of Stream Dry frame to indicate the stream's previous
interruption is ended.

### Client Information frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------------------------------+----------------------+
| 0x12  | Time Since Play Start Ms (32) | Payload ...
+-------+-------------------------------+----------------------+
~~~

Time Since Play Start in Ms:
: time elapsed since beginning of playback session, in milliseconds.

Payload:

: JSON containing relevant client information, such as time since last
stall, time since last play, buffer size, max resolution supported or list of
codecs supported.

TODO: Document JSON schema?

Player sends the Client Information frame regularly to server to be used in ABR.

### Application Specific Data frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------+----------------------------------------------+
| 0x13  |Subtype|
+-------+-------+----------------------------------------------+
|                       PTS (64)                               |
+--------------------------------------------------------------+
| Payload ...
+--------------------------------------------------------------+
~~~


SubType:
: enum identifying the application specific use case

TODO: Enum value registry?

PTS:
: presentation timestamp in connection video timescale

Payload:
: generic application specific data

Generic payload that contains application specific data with a subtype to
identify the use case.

## Quic Mapping

Quic mapping works differently in normal mode v.s. multi-stream mode. In normal
mode, there is one single QUIC stream and every frame is in this stream. The
following describes the more complicated multi-stream mode.

There should be 1 QUIC stream per frame/audio sample.  The first frame must be a
Connect frame.  After that Video frames and Audio frames will follow using the
following rules.

 * Stream (audio or video) decode time X must be in a higher stream then any
   decode times before it.
 * There currently is no cross stream synchronization of the streams.

Response Streams, Connect Ack and Error, will be in the response stream of the
stream that sent it.

The mapping code from QUIC → Streaming protocol will handle out of order frames
by waiting for the next stream for now.

# Error Handling

# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.



--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
