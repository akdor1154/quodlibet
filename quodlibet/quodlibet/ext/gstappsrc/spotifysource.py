from gi.repository import Gst, GstApp
from quodlibet.util.dprint import print_d
from quodlibet.plugins.gstappsrc import AppSrcPlugin

import spotify
import quodlibet

class SpotifySource(AppSrcPlugin, spotify.sink.Sink):
    PLUGIN_ID = "spotify-appsrc"
    PLUGIN_NAME = _("Spotify Play Component")
    PLUGIN_DESC = _("Handles playing files with a spotify: protocol")

    uri_protocol = 'spotify'

    def source_setup(self, playbin, appsrc):
        super(SpotifySource, self).source_setup(playbin, appsrc)
        self._appsrc.set_caps(self._caps)
        self._appsrc.set_stream_type(GstApp.AppStreamType.SEEKABLE)
        self._appsrc.set_property('format', Gst.Format.TIME)
        self._appsrc.set_property('max-bytes', 100000)
        self._appsrc.set_property('block', False)

        self._is_setup = True
        if self._play_after_setup is not None:
            self._play_after_setup()
            self._play_after_setup = None

    def __init__(self, player, playbin):
        super(SpotifySource, self).__init__(player, playbin)
        print_d('made spotify src')
        self._session = quodlibet.spotify
        self._play_after_setup = None
        self._is_setup = False

        self._caps = Gst.Caps.from_string('''
audio/x-raw,
format=(string)S16LE,
channels=(int)2,
rate=(int)44100,
layout=(string)interleaved
''')
        # Quodlibet will spawn a new sink if gapless is not being used.
        # Hence, we need to tell the session to forget any old sinks.
        self._session.off(spotify.SessionEvent.MUSIC_DELIVERY)
        self._session.on(spotify.SessionEvent.END_OF_TRACK, self._track_ended)
        self._song = None
        self._playing = False
        self._have_enough_data = False
        self._stamp = 0
        self._frames = 0

    def _enough_data(self, *args):
        self._have_enough_data = True

    def _need_data(self, *args):
        self._have_enough_data = False

    def on(self):
        super(SpotifySource, self).on()

    def off(self):
        super(SpotifySource, self).off()

    def _on_music_delivery(self, session, audio_format, frames, num_frames):
        print_d('f')
        if (self._have_enough_data):
            return 0
        if frames is None:
            print_d('frames was none :(')
            return 0
        if num_frames == 0:
            print_d('no frames to send -- this happens after a seek')
            return 0

        buffer = Gst.Buffer.new_wrapped(frames)

        # duration is in nanoseconds, thanks gstreamer
        buffer.duration = round(num_frames * 1000000000.0
                                / audio_format.sample_rate)

        buffer.pts = self._stamp

        # buffer.offset = self._frames
        # buffer.offset_end = self._frames + num_frames

        result = self._appsrc.push_buffer(buffer)
        if result != Gst.FlowReturn.OK:
            print_d('frame not pushed: '+repr(result))
            return 0

        self._frames += num_frames
        self._stamp = self._stamp + buffer.duration

        return num_frames

    def _on_message(self, sender, message):
        # print_d('message: '+str(message.type))
        pass

    def _close(self):
        self.off()

    def play_song(self, song):
        super(SpotifySource, self).play_song(song)

    def _start_song(self, song):
        print_d('helloz. playing %s' % song._sp_track.name)
        self._song = song
        self._playing = True
        self._have_enough_data = False
        self._stamp = 0
        self._frames = 0

        if self._session.num_listeners(spotify.SessionEvent.MUSIC_DELIVERY) == 0:
            print_d('need to turn on')
            self.on()

        # preload the spotify song
        song._sp_track.load()
        self._session.player.load(song._sp_track)

        # it works without all the new stream and new segment events,
        # but it seems to be the Right Thing To Do, and gstreamer
        # documentation is quite poor on how stuff copes without them
        stream_id = self._src_pad.create_stream_id(self._appsrc, song('~uri'))
        start_stream = Gst.Event.new_stream_start(stream_id)

        self._appsrc.send_event(start_stream)

        # actually play!
        self._appsrc.set_state(Gst.State.PLAYING)
        self._session.player.play()

    def _stop_song(self, player, song, stopped):
        self._playing = False
        print_d('stopped!'+str(stopped))
        if stopped:
            self._session.player.unload()
        print_d('finished song stop')
        # self._session.off(spotify.SessionEvent.MUSIC_DELIVERY)

    def _seek_data(self, appsrc, seekNS):

        seekMS = seekNS / 1000000
        self._session.player.seek(seekMS)
        self._stamp = seekNS

        return True

    def _pause(self, player=None):
        if self._playing:
            print_d('paused by signal')
            self._session.player.pause()
            self._playing = False

    def _resume(self, player=None):
        if not self._playing:
            print_d('resumed by signal')
            self._session.player.play()
            self._playing = True

    def _track_ended(self, session):
        if self._playing:
            print_d('we\'re done here')
            self._appsrc.end_of_stream()
            self._playing = False
