# Name: Media Over QUIC
# Description
There are video/media related use-cases that do not appear to be well met by existing protocols.

## Media Ingest Use Case
Example: live stream broadcast, with later video-on-demand playback.

**Requirements:**
1. Have a mechanism to tune latency/quality tradeoffs. 
2. Have a mechanism to allow bitrate adaptation in the encoders. The adaptation can also be based on latency/quality tradeoffs. 
3. Able to support low latency in the range of 500ms - 1s. 
4. Able to support high quality such as 4K HDR 
5. Able to support new video/audio codecs in the future. 
6. Frame-based, not chunk-based, i.e. frames are sent out immediately as they are available. 
7. Able to support live captions and cuepoints for Ad insertions. 
8. Supports switching networks. (ex. WiFi => cellular) 
9. Support “server migration”: a mechanism that allows clients to continue ingest even if servers on the ingest path need to restart for maintenance/etc.

**Existing Protocols/Challenges:**
1. RTMP: The standard is a bit stagnant and doesn’t have an official way to add new codecs support. It’s TCP based which has the head-of-line blocking issue and can’t use newer congestion control algorithms such as BBR. 
2. RTC/WebRTC: Doesn’t have an easy way to tune latency/quality tradeoffs and the existing protocol sacrifices too much quality for latency which is not suitable for live streams with premium content. Requires SDP exchange between peers which is unnecessary for client server live streaming use cases. 
3. HTTP based protocols (HLS, DASH): Chunk-based protocols incur more latency. These protocols are defined for delivery, but have also been used for ingestion in some cases as well.

## Large-scale Media Playback Use Case
Example: 10k+ viewers watching a live broadcast with different quality networks 

**Requirements:**
1. Same as media ingest. 
2. Browser playback support. 
3. Able to automatically choose the best rendition for playback. (ABR) 
4. Able to drop media during severe congestion/starvation. 
5. Does not rely on encoder feedback. 
6. Minimal handshake RTTs and fast playback start. 
7. CDN support is possible. 
8. Support for timed metadata 
9. Support for media seeking

**Existing Protocols/Challenges:**
1. HTTP based protocols (HLS, DASH): Head-of-line blocking and chunk-based protocols incur more latency. Low latency client-side ABR algorithms are unable to determine if the stream is network bound or encoder bound, limiting their effectiveness. 
2. RTP/WebRTC: 
    1. Focused on real-time latency and doesn’t have a way to tune latency/quality tradeoffs. 
    2. Peer-to-peer support complicates everything: long handshake, blocked by corporate firewalls, no roaming support, port per connection. Frame dropping requires encoder feedback (Full Intra Request) or minimal reference frames (lower quality) otherwise it causes artifacting. 
    3. No b-frame support for higher quality/latency video. 
    4. Cannot easily leverage CDN infrastructure. 
    5. Tight coupling between media framing and transport. 
3. Others: No browser support.

## BoF Goal
The purpose of this BoF is to:

1. Determine if there is an existing protocol that can meet these use cases and requirements.
2. If not, is there an existing protocol that could be easily extended to meet these use cases
3. If not, is there agreement we should forge a new protocol to meet these use cases
4. If so, determine whether an existing working group or a new working group is best suited to work on this protocol.

# Required Details
* Status: not WG Forming
* Responsible AD: Murray Kucherawy
* BOF proponents: Alan Frindell afrind@fb.com, Ying Yin yingyin@google.com
* BOF chairs: Magnus Westerlund, Alan Frindell
* Number of people expected to attend: 50
* Length of session (1 or 2 hours): 2 hours
* Conflicts (whole Areas and/or WGs)
* Chair Conflicts: quic, webtransport, masque, ohai
* Technology Overlap: quic, mops, avtcore, mmusic
* Key Participant Conflict: webtransport, masque

# Agenda
1. Administrative Details (5m) 
    1. Note Well 
    2. Note taker, Jabber relay
2. Use cases (20m) 
    1. Present Media Ingest and Playback use cases not well covered by existing protocols 
    2. Discussion of use cases
3. BoF Questions and Discussion (30m) 
    1. Does an existing protocol cover these use cases? 
    2. Can an existing protocol be extended to cover these use cases? 
    3. Should we create a new protocol to cover these use cases? 
    4. Should an existing working group take on this work or should we form a new working group?
4. Wrap Up and Next Steps (5m)

# Links to the mailing list, draft charter if any, relevant Internet-Drafts, etc.
* Mailing List: https://www.ietf.org/mailman/listinfo/moq
* Draft charter: Not WG Forming
* Relevant drafts:
    * Use Cases:
        * https://fiestajetsam.github.io/2021/08/22/quic-video.html
    * Solutions
        * RUSH - https://datatracker.ietf.org/doc/draft-kpugin-rush/
        * WARP - https://www.ietf.org/archive/id/draft-lcurley-warp-00.html, https://www.youtube.com/watch?v=hG0nmy3Otg4
