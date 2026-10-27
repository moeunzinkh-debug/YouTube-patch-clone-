/*
 * Copyright 2026 Morphe.
 * https://github.com/MorpheApp/morphe-patches
 *
 * See the included NOTICE file for GPLv3 Section 7 terms that apply to this code.
 */

package app.morphe.patches.shared.misc.compat

import app.morphe.patcher.InstructionLocation

/**
 * Backports of the two Patcher 2.0 [InstructionLocation] variants used by the
 * YouTube patches added from upstream v1.48.0. This repository still builds
 * against morphe-patcher 1.14.0, where [InstructionLocation] is a `fun interface`
 * with only `indexIsValidForMatching`.
 *
 * Patcher 1.14.0 only searches forwards, so [MatchBeforeImmediately] is an
 * approximation; it is used by a single SponsorBlock fingerprint. Removing this
 * file requires migrating the whole project to Patcher 2.0.
 */
class MatchAfterLast : InstructionLocation {
    override fun indexIsValidForMatching(previouslyMatchedIndex: Int, currentIndex: Int): Boolean =
        currentIndex > previouslyMatchedIndex
}

class MatchBeforeImmediately : InstructionLocation {
    override fun indexIsValidForMatching(previouslyMatchedIndex: Int, currentIndex: Int): Boolean =
        previouslyMatchedIndex >= 0 && currentIndex == previouslyMatchedIndex - 1
}
