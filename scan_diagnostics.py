"""Local capture diagnostics; no model client, keys or network access."""
import json

DETECTOR_VERSION = 'tooltip-grid-2'


def save_diagnostics(path, *, screen, requested_mode, effective_mode, bounds,
                     state, message, request_id):
    payload = dict(
        detector_version=DETECTOR_VERSION, request_id=request_id,
        resolution=list(screen.size), cursor=screen.info.get('cursor'),
        requested_mode=requested_mode, effective_mode=effective_mode,
        crop_bounds=bounds, state=state, message=message,
    )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    from PIL import Image
    from capture_regions import resolve_scan_mode, crop_for_ai, _check_rune_grid_presence
    from tooltip_detection import tooltip_candidates

    parser = argparse.ArgumentParser(description='Replay local detection without AI or database writes.')
    parser.add_argument('screenshot', type=Path)
    parser.add_argument('--mode', default=None)
    args = parser.parse_args()
    sidecar = args.screenshot.with_suffix('.json')
    metadata = json.loads(sidecar.read_text(encoding='utf-8')) if sidecar.exists() else {}
    with Image.open(args.screenshot) as source:
        screen = source.convert('RGB')
    if metadata.get('cursor') is not None:
        screen.info['cursor'] = metadata['cursor']
    mode = args.mode or metadata.get('requested_mode', 'stash')
    report = dict(detector_version=DETECTOR_VERSION, resolution=screen.size,
                  requested_mode=mode, candidates=tooltip_candidates(screen),
                  rune_grid=_check_rune_grid_presence(screen))
    report['effective_mode'] = resolve_scan_mode(screen, mode)
    try:
        _, report['crop_bounds'] = crop_for_ai(screen, report['effective_mode'])
    except ValueError as error:
        report['rejection'] = str(error)
    print(json.dumps(report, ensure_ascii=False, indent=2))
