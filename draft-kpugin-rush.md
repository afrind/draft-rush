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
    ins: K. Pugin
    name: Kirill Pugin
    organization: Facebook
    email: ikir@fb.com
 -
    ins: A. Frindell
    name: Alan Frindell
    organization: Facebook
    email: afrind@fb.com
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

RUSH is an application-level protocol for ingesting live video.
This document describes core of the protocol and how it maps onto QUIC

--- middle

# Introduction

RUSH is bidirectional application level protocol designed for live video
ingestion that runs on top of QUIC.

RUSH was built as a replacement for RTMP (Real-Time Messaging Protocol) with the
goal to provide support for new audio and video codecs, extensibility in form of
new message types, multi-track support. In addition, RUSH gives applications
option to control data delivery guarantees by utilizing QUIC streams.

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

## Connection establishment

In order to live stream using RUSH, client should establish QUIC connection
first.

After QUIC connection is established, client creates new QUIC stream, choses
starting frame ID and sends `Connect frame` over that stream.

## Sending data

Client MAY not wait for `ConnectAck frame` and start sending data immediately.
Client takes encoded audio or video data, increment previously sent frame ID for
a given track and serialize that in appropriate frame format ({{audio-frame}},
{{video-frame}}).

Timestamp fields MUST be in a timescale specified by `Connect frame`.

Depending on mode of operation ({{quic-mapping}}), client reuses QUIC stream
that was used to send `Connect frame` or it creates new QUIC stream. Once QUIC
stream is selected, client sends data over that stream.

Client MAY continue sending audio, video data.

In `Multi stream mode` client may decide to stop sending frame by closing
corresponding QUIC stream. There is no guarantee in this case that data were or
were not received by the server.

## Receiving data

Upon receiving `Connect frame`, server replies with `ConnectAck frame` and
prepares to recieve audio/video data.

It's possible that in `Multi stream mode` ({{multi-stream-mode}}), server
receives audio or video data before it receives `Connect frame`, it's up to
implementation to decide how to deal with that. General recommendation is to
wait for `Connect frame` before using any audio/video data as they cannot be
interpret correctly.

In `Normal mode` ({{normal-mode}}) it is guaranteed by the transport that frames
arrive into application layer in order they were sent, so any gaps in frame
sequence IDs for a given track are indication of error on sending side.

In `Multi stream mode` it's possible that frames arrive to application layer out
of order they were sent, therefore server MUST keep track of last received frame
ID for every track that it receives. Gap in frame sequence ID on a given track
MAY indicate out of order delivery and server MAY wait until missing frames
arrive. Server must consider frame completely lost if corresponding QUIC stream
was closed.

## Reconnect

At any point if QUIC connection is closed, client may reconnect by simply
repating `Connection establishment` process ({{connection-establishment}}).

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

Length(64)`:
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
| 0x2 | reserved |
| 0x3 | reserved |
| 0x4 | reserved |
| 0x5 | error frame |
| 0x6 | reserved |
| 0x7 | reserved |
| 0x8 | reserved |
| 0x9 | reserved |
| 0xA | reserved |
| 0XB | reserved |
| 0xC | reserved |
| 0xD | video frame |
| 0xE | audio frame |
| 0XF | reserved |
| 0X10 | reserved |
| 0x11 | reserved |
| 0x12 | reserved |
| 0x13 | reserved |

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
: identifier of broadcast, when reconnect, client MUST use the same live session
ID

Payload:
: application and version specific data that can be used by server. OPTIONAL

This is frame used by a client. It sends a connect frame to initiate
broadcasting. The client can start sending other frames right after "Connect
frame" without waiting acknowledgement from the server.

If server doesn't support VERSION sent by the client, server sends error frame
with code `UNSUPPORTED VERSION`

If audio time scale or video timescale are 0, server sends error frame with
error code `INVALID FRAME FORMAT` and closes connection.

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

There can be only one "Connect Ack" frame sent over lifetime of the QUIC
connection.

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


### Video frame

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
: Distance from sequence ID of the I-frame that is required before this frame
can be decoded. This can be useful to decide if frame can be dropped.


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

Binary concatenation of "video data" from consecutive video frames, without data
loss MUST produce VALID h264/h265 bitstream.


### Audio frame

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

For AAC codec, "Audio Data" are 1 or more AAC samples, prefixed with ADTS
HEADER:

~~~
152        158       ...     N
+---+---+---+---+---+---+---+...
| ADTS(56)  |  AAC SAMPLE   |
+---+---+---+---+---+---+---+...
~~~

Binary concatenation of all AAC samples in "Audio Data" from consecutive audio
frames, without data loss MUST produce VALID AAC bitstream.

For OPUS codec, "Audio Data" are 1 or more OPUS samples, prefixed with OPUS
header as defined in {{!RFC7845}}


## Quic Mapping

One of the main goals of the RUSH protocol was ability to provide applications a
way to control reliablity of delivering audio/video data. This is achieved by
special mode {{multi-stream-mode}}.

### Normal mode

In normal mode RUSH uses one QUIC stream to send data and one QUIC stream to
receive data. Using one stream guarantees reliable, in-order delivery -
applications can rely on QUIC transport layer to retransmit lost packets.

### Multi stream mode

In normal mode, if packet belonging to video frame is lost, all packets sent
after it will not be delivered to application, even though those packets may
have arrived to receiving QUIC endpoint. This introduces head of line blocking
and can negatively impact latency.

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

Application MAY control delivery reliability by setting delivery timer for every
audio or video frame and close QUIC stream when timer fires - this will
effectively stop retransmissions if frame wasn't fully delivered in time.


# Error Handling

An endpoint that detects an error SHOULD signal the existence of that error to
its peer.  Errors can affect an entire connection (see {{connection-errors}}),
or a single frame (see {{frame-errors}}).

The most appropriate error code SHOULD be included in the error frame that
signals the error.


## Connection errors

There is one error code defined in core of the protocol that indicates
connection error:

1 - UNSUPPORTED VERSION - indicates that server doesn't support version
specified in Connect frame


## Frame errors

There are two error codes defined in core of the protocol that indicates
problems with particular frame:

2 - UNSUPPORTED CODEC - indicates that server doesn't support audio or video
codec

3 - INVALID FRAME FORMAT - indicates that receiver was not able to parse frame
or there was an issue with fields' values.

# Extensions

RUSH permits extension of the protocol.

Extensions are permitted to use new frame types ({{wire-format}}), new error
codes ({{error-frame}}), new audio and video codecs ({{audio-frame}},
{{video-frame}}).

Implementations MUST ignore unknown or unsupported values in all extensible
protocol elements.  Implementations MUST discard frames that have unknown or
unsupported types.  This means that any of these extension points can be safely
used by extensions without prior arrangement or negotiation.

# Security Considerations

RUSH protocol relies on security guarantees provided by the transport.

Implementation SHOULD be prepare to handle cases when sender deliberately sends
frames with gaps in sequence IDs.

Implementation SHOULD be prepare to handle cases when server never receives
Connect frame ({{connect-frame}}).

A frame parser MUST ensure that value of frame length field (see
{{frame-header}}) matches actual length of the frame, including the frame
header.

Implementation SHOULD be prepare to handle cases when sender sends a frame with
large frame length field value.


# IANA Considerations

TODO: add frame type registery, error code registery, audio/video codecs
registery



--- back

# Acknowledgments
{:numbered="false"}

This draft is work of many people: Vlad Shubin, Nitin Garg, Milen Lazarov, Benny Luo, Nick Ruff, Konstantin Tsoy, Nick Wu.
