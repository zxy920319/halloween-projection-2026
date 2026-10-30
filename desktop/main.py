import argparse
import asyncio
import logging
import threading
import time

from desktop.ingest import FrameIngestServer

LOG = logging.getLogger("desktop")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Desktop frame ingest and optional preview")
    parser.add_argument("--host", default="127.0.0.1", help="bind address; default is loopback only")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--preview", action="store_true", help="show a local Tk preview window")
    parser.add_argument("--pose", action="store_true", help="run MediaPipe pose and publish /poses")
    parser.add_argument("--model", default="models/pose_landmarker_lite.task")
    parser.add_argument("--pose-host", default="127.0.0.1")
    parser.add_argument("--pose-port", type=int, default=8766)
    return parser.parse_args()


def build_pose_processor(args):
    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator
    from desktop.pose.publisher import PosePublisher, pose_to_json

    estimator = MediaPipePoseEstimator(args.model)
    publisher = PosePublisher()
    publisher.start(args.pose_host, args.pose_port)
    stats = {"n": 0, "t": time.monotonic()}

    def process(frame):
        pose = estimator.estimate(frame)
        publisher.publish(pose_to_json(pose))
        stats["n"] += 1
        now = time.monotonic()
        if now - stats["t"] >= 2:
            LOG.info("pose fps=%.1f persons=%d", stats["n"] / (now - stats["t"]), len(pose.persons))
            stats["n"], stats["t"] = 0, now
        return pose

    return process


def run_pose_loop(ingest, process, thread) -> None:
    import queue

    try:
        while thread.is_alive():
            try:
                frame = ingest.store.queue.get(timeout=1)
            except queue.Empty:
                continue
            process(frame)
    except KeyboardInterrupt:
        LOG.info("stopped by user")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("port must be in 1..65535")
    ingest = FrameIngestServer()
    ready = threading.Event()
    startup_error: list[OSError] = []

    def run_server() -> None:
        try:
            asyncio.run(ingest.run(args.host, args.port, ready))
        except OSError as exc:
            startup_error.append(exc)
            LOG.exception("could not bind ingest server to %s:%d", args.host, args.port)
        finally:
            ready.set()

    thread = threading.Thread(target=run_server, name="frame-ingest", daemon=True)
    thread.start()
    if not ready.wait(timeout=5):
        raise SystemExit("timed out waiting for the frame server to start")
    if startup_error:
        raise SystemExit(f"could not start frame server: {startup_error[0]}")
    process = build_pose_processor(args) if args.pose else None
    if args.preview:
        from desktop.preview import PreviewWindow

        PreviewWindow(ingest.store, process).run(thread)
    elif process is not None:
        run_pose_loop(ingest, process, thread)
    else:
        try:
            while thread.is_alive():
                time.sleep(1)
                LOG.info(
                    "received=%d queued=%d dropped=%d",
                    ingest.received_frames,
                    ingest.store.queue.qsize(),
                    ingest.store.dropped_frames,
                )
            raise SystemExit("frame server stopped unexpectedly")
        except KeyboardInterrupt:
            LOG.info("stopped by user")


if __name__ == "__main__":
    main()
