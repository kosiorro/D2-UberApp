"""Local tooltip detection, independent of Windows, the database and AI.

Coordinates are always in source pixels. Text colours are only geometric
evidence; item names and properties are still read and validated by the model.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class TextLine:
    left: int
    top: int
    right: int
    bottom: int
    coloured: int
    pixels: int

    @property
    def centre(self):
        return (self.left + self.right) / 2


def _runs(mask):
    changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    return zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1))


def _text_masks(rgb):
    # Include antialiasing near the solid glyph cores, without treating all
    # bright game scenery as text. Do not recolour the image sent to AI.
    arr = rgb.astype(np.int32)
    colours = ((110, 110, 255), (199, 179, 119), (0, 255, 0),
               (255, 0, 0), (255, 77, 77), (255, 255, 100), (255, 168, 0))
    coloured = np.zeros(arr.shape[:2], dtype=bool)
    intensity = np.max(arr, axis=2)
    for colour in colours:
        # Follow the colour down the antialiased edge of a letter. Looking
        # only for exact solid pixels loses glyphs after UI scaling/resizing.
        peak = max(colour)
        matches = (intensity >= .6 * peak) & (intensity <= 1.08 * peak)
        for channel, value in enumerate(colour):
            matches &= np.abs(arr[:, :, channel] * peak - intensity * value) <= 12 * peak
        coloured |= matches
    white = (np.min(arr, axis=2) >= 170) & (np.ptp(arr, axis=2) <= 12)
    return white | coloured, coloured


def _text_lines(mask, coloured, scale):
    """Join letters horizontally, but never bridge the space between lines."""
    radius = max(3, round(18 * scale))
    padded = np.pad(mask, ((0, 0), (radius, radius)))
    sums = np.pad(np.cumsum(padded, axis=1, dtype=np.int32), ((0, 0), (1, 0)))
    joined = sums[:, 2 * radius + 1:] - sums[:, :-(2 * radius + 1)] > 0
    components = []
    previous = []
    parents = []

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for y, row in enumerate(joined):
        current = []
        for start, end in _runs(row):
            touching = {root(i) for a, b, i in previous if a < end and b > start}
            if not touching:
                i = len(components)
                parents.append(i)
                components.append([start, y, end, y + 1])
            else:
                i = min(touching)
                for other in touching - {i}:
                    parents[other] = i
                    a, b, c, d = components[other]
                    box = components[i]
                    box[:] = [min(box[0], a), min(box[1], b), max(box[2], c), max(box[3], d)]
                box = components[i]
                box[:] = [min(box[0], start), box[1], max(box[2], end), y + 1]
            current.append((start, end, i))
        previous = current

    lines = []
    for i, (left, top, right, bottom) in enumerate(components):
        if root(i) != i or not 10 * scale <= bottom - top <= 32 * scale:
            continue
        ys, xs = np.where(mask[top:bottom, left:right])
        if len(xs) < 12 * scale or not len(xs):
            continue
        x0, x1 = left + int(xs.min()), left + int(xs.max()) + 1
        if x1 - x0 < 24 * scale:
            continue
        if not .06 <= len(xs) / ((x1 - x0) * (bottom - top)) <= .65:
            continue
        colour_count = int(coloured[top:bottom, x0:x1].sum())
        lines.append(TextLine(x0, top, x1, bottom, colour_count, len(xs)))
    return sorted(lines, key=lambda line: (line.top, line.left))


def _frames(rgb, scale):
    """Pair horizontal borders, including borders touching screen edges."""
    height, width = rgb.shape[:2]
    edges = []
    for y, row in enumerate(rgb):
        flat = np.max(np.abs(np.diff(row.astype(np.int16), axis=0)), axis=1) <= 2
        for start, end in _runs(flat):
            if end - start < 90 * scale:
                continue
            pixel = row[(start + end) // 2].astype(int)
            if 20 <= pixel[0] <= 130 and np.ptp(pixel) <= 22:
                edges.append((int(start), y, int(end) + 1))
    frames = []
    for i, (left, top, right) in enumerate(edges):
        for x, bottom, r in edges[i + 1:]:
            if 45 * scale <= bottom - top <= height * .98:
                if abs(x - left) <= 8 * scale and abs(r - right) <= 8 * scale:
                    frames.append((min(x, left), top, max(r, right), bottom + 1))
    return frames


def tooltip_candidates(image):
    """Return tightly bounded, plausible complete text blocks (x, y, w, h)."""
    rgb = np.asarray(image.convert('RGB'))
    height, width = rgb.shape[:2]
    scale = max(.5, min(width / 1920, height / 1080))
    mask, coloured = _text_masks(rgb)
    lines = _text_lines(mask, coloured, scale)
    clusters = []
    for line in lines:
        matches = []
        for cluster in clusters:
            last = cluster[-1]
            gap = line.top - last.bottom
            centre = float(np.median([entry.centre for entry in cluster]))
            if 0 <= gap <= 45 * scale and abs(line.centre - centre) <= 28 * scale:
                matches.append((abs(line.centre - centre), cluster))
        if matches:
            min(matches, key=lambda entry: entry[0])[1].append(line)
        else:
            clusters.append([line])

    candidates = []
    frames = None
    for cluster in clusters:
        if len(cluster) < 3:
            continue
        if np.median([line.bottom - line.top for line in cluster]) < 12 * scale:
            continue
        if np.median([line.right - line.left for line in cluster]) < 80 * scale:
            continue
        left = min(line.left for line in cluster)
        right = max(line.right for line in cluster)
        top, bottom = cluster[0].top, cluster[-1].bottom
        if bottom - top < 45 * scale or right - left < 160 * scale:
            continue
        # Tooltips are compact centred text on a darkened background. A row of
        # runes or a stat panel does not satisfy the coloured-line evidence.
        colour_lines = sum(line.coloured >= max(12 * scale, line.pixels * .45) for line in cluster)
        if colour_lines < 2:
            # Plain white/grey items need geometric border evidence, not a
            # coloured name. This also avoids mistaking stat-panel columns.
            if frames is None:
                frames = _frames(rgb, scale)
            if not any(x <= left and r >= right and y <= top and b >= bottom
                       and top - y <= 50 * scale and b - bottom <= 100 * scale
                       and abs((x + r) / 2 - (left + right) / 2) <= 20 * scale
                       for x, y, r, b in frames):
                continue
        sub = rgb[top:bottom, left:right]
        if np.mean(np.max(sub, axis=2) < 90) < .65:
            continue
        # Grey base names (e.g. socketed items) must survive a crop even when
        # they precede the first bright line. Grey action hints use a different
        # shade, and are deliberately not part of this extension.
        centre = float(np.median([line.centre for line in cluster]))
        sx, sy = max(0, int(left - 40 * scale)), max(0, int(top - 65 * scale))
        sr, sb = min(width, int(right + 40 * scale)), min(height, int(bottom + 45 * scale))
        grey_rgb = rgb[sy:sb, sx:sr].astype(np.int16)
        grey = ((np.min(grey_rgb, axis=2) >= 63)
                & (np.max(grey_rgb, axis=2) <= 110)
                & (np.ptp(grey_rgb, axis=2) <= 5))
        grey_lines = []
        for line in _text_lines(grey, grey, scale):
            pixels = grey_rgb[line.top:line.bottom, line.left:line.right]
            # Antialiased action hints (solid grey 144) also contain some 105
            # pixels. Require a genuinely dim line, not just dim glyph edges.
            brighter = (np.min(pixels, axis=2) > 125) & (np.ptp(pixels, axis=2) < 12)
            if brighter.sum() <= line.coloured * .2:
                grey_lines.append(line)
        for line in reversed(grey_lines):
            if cluster[0].coloured >= 12 * scale:
                break
            if abs(line.centre + sx - centre) > 28 * scale:
                continue
            if 0 <= top - line.bottom - sy <= 45 * scale:
                top = line.top + sy
                left, right = min(left, line.left + sx), max(right, line.right + sx)
        for line in grey_lines:
            if abs(line.centre + sx - centre) <= 28 * scale and 0 <= line.top + sy - bottom <= 35 * scale:
                bottom = line.bottom + sy
                left, right = min(left, line.left + sx), max(right, line.right + sx)
        margin = max(4, round(10 * scale))
        bounds = (max(0, left - margin), max(0, top - margin),
                  min(width, right + margin), min(height, bottom + margin))
        x, y, r, b = bounds
        candidates.append(tuple(map(int, (x, y, r - x, b - y))))
    return candidates


def find_tooltip_crop(image, strict=False, mode='normal', cursor=None):
    """Select one tooltip; never substitute a full screen for a failed crop."""
    candidates = tooltip_candidates(image)
    if strict and candidates:
        # Used by rune scans as a presence check, not for choosing an item.
        return candidates[0]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None
    # Comparisons can show multiple descriptions. Only disambiguate when one
    # candidate is clearly nearer the captured cursor; otherwise ask to retry.
    if cursor is not None:
        cx, cy = cursor

        def distance(box):
            x, y, w, h = box
            return max(x - cx, 0, cx - x - w) ** 2 + max(y - cy, 0, cy - y - h) ** 2

        ordered = sorted(candidates, key=distance)
        if distance(ordered[0]) + 40 ** 2 < distance(ordered[1]):
            return ordered[0]
    return None
