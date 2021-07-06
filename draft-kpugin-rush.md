---
title: "RUSH - Reliable (unreliable) streaming protocol"
abbrev: "rush"
docname: draft-kpugin-rush-latest
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

RUSH is bidirectional application level protocol designed for live video ingestion that runs on top of QUIC. 

RUSH was built as a replacement for RTMP (Real-Time Messaging Protocol) with the goal to provide support for new audio and video codecs, extensibility in form of new message types, multi-track support. In addition, RUSH gives applications option to control data delivery guarantees by utilizing QUIC streams.

This document describes core of RUSH protocol, wire format, and QUIC mapping.

# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in BCP 14 {{RFC2119}} {{!RFC8174}}
when, and only when, they appear in all capitals, as shown here.

Frame/Message:

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

ASC:

: Audio specific config


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
|Type(8)| Payload ...                                          |
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
...
| 0x5 | error frame |
| 0xD | video frame |
| 0xE | audio frame |
...
| 0x13 | application specific data frame |

## Frames

### Connect frame

~~~
+--------------------------------------------------------------+
|                       Length (64)                            |
+--------------------------------------------------------------+
|                       ID (64)                                |
+-------+-------+---------------+---------------+--------------+
| 0x0   |Version|Video Timescale|Audio Timescale|              |
+-------+-------+---------------+---------------+--------------+
|                    Live Session ID(64)                       |
+--------------------------------------------------------------+
| Payload ...                                                  |
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

Live Session ID:
: identifier of broadcast, when reconnect, client MUST use the same live session ID

Payload:
: application and version specific data that can be used by server. OPTIONAL

This is frame used by a client. It sends a connect frame to initiate
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
| I-Frame ID Offset | Video Data ...                           |
+---------------+----------------------------------------------+
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
|0x3| VP8|
|0x4| VP9|


Track ID:
: ID of the track that this frame is on

I-Frame ID Offset:
: Distance from sequence ID of the I-frame that is required before this frame can
be decoded. This can be useful to decide if frame can be dropped.


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

Codec:
: specifies codec that was used to encode this frame.

Supported type of codecs:

| Type| Codec|
|-----|------|
|0x1| AAC|
|0x2| OPUS|

Timestamp:
: timestamp of first audio sample in Audio Data.  TODO: describe format

Track ID:
: ID of the track that this frame is on

Audio Data:
: variable length field, that carries 1 or more audio frames that is codec
dependent.

For AAC codec, "Audio Data" are 1 or more AAC samples, prefixed with ADTS HEADER:

~~~
152        158       ...     N
+---+---+---+---+---+---+---+...
| ADTS(56)  |  AAC SAMPLE   |
+---+---+---+---+---+---+---+...
~~~

Binary concatenation of all AAC samples in "Audio Data" from consecutive audio
frames, without data loss MUST produce VALID AAC bitstream.


For OPUS codec, "Audio Data" are 1 or more OPUS samples, prefixed with 
OPUS header as defined in {{RFC7845}}

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
identify the use case and can be used to add new type of frames.


## Quic Mapping

One of the main goals of the RUSH protocol was ability to provide applications a way 
to control reliablity of delivering audio/video data. This is achieved by special
mode {{multi-stream-mode}.

### Normal mode

In normal mode RUSH uses one QUIC stream to send data and one QUIC stream 
to receive data. Using one stream guarantees reliable, in-order delivery - applications
can rely on QUIC transport layer to retransmit lost packets.

### Multi stream mode

In normal mode, if packet belonging to video frame is lost, all packets sent after it 
will not be delivered to application, even though those packets may have arrived
to receiving QUIC endpoint. This introduces head of line blocking and can 
negatively impact latency.

To address this problem, RUSH defines "multi-stream" mode, in which one QUIC
stream is used per audio/video frame.

Connection establishment follows normal procedure by client sending Connect
frame, after that Video and Audio frams are sent using following rules:

* Each new frame is send on new QUIC stream
* Frames within same track must have IDs that are monotonically increasing,
such that ID(n) = ID(n-1) + 1

Receiver SHOULD order frames within a track using frames IDs.

Response Streams, Connect Ack and Error, will be in the response stream of the
stream that sent it.

Application MAY control delivery reliability by setting delivery timer for every audio
or video frame and close QUIC stream when timer fires - this will effectively stop
retransmissions if frame wasn't fully delivered in time.


# Error Handling

An endpoint that detects an error SHOULD signal the existence of that error to its peer. 
Errors can affect an entire connection (see {{connection-errors}}), or a single frame (see {{frane-errors}}).

The most appropriate error code SHOULD be included in the error frame that signals the error.


## Connection errors
There is one error code defined in core of the protocol that indicates connection error:

1 - UNSUPPORTED VERSION - indicates that server doesn't support version specified in Connect frame


## Frame errors

There are two error codes defined in core of the protocol that indicates problems with particular frame:

2 - UNSUPPORTED CODEC - indicates that server doesn't support audio or video codec

3 - INVALID FRAME FORMAT - indicates that receiver was not able to parse frame


# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.



--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
