package app.morphe.patches.simsimi

import java.io.File
import java.security.MessageDigest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class AdGateTransformTest {
    private fun source() = File(System.getenv("SIMSIMI_HBC_FIXTURE") ?: error("Exact fixture required")).readBytes()
    private fun assertFooter(bytes: ByteArray) {
        val end = bytes.size - 20
        assertContentEquals(MessageDigest.getInstance("SHA-1").digest(bytes.copyOfRange(0, end)), bytes.copyOfRange(end, bytes.size))
    }

    @Test fun recognizesOnlyThePinned923Or926Payload() {
        val source = source()
        assertTrue(AdGateTransform.profileVersion(source) in setOf("9.2.3", "9.2.6"))
        assertTrue(source.size in setOf(AdGateTransform.EXPECTED_SIZE, AdGateTransform.V926_EXPECTED_SIZE))
        assertFooter(source)
    }

    @Test fun sixFeatureGatesAreExactAndCompose() {
        val source = source()
        assertEquals(6, AdGateTransform.featureKeys.size)
        for (key in AdGateTransform.featureKeys) {
            val patched = AdGateTransform.patchFeature(source, key)
            val ranges = AdGateTransform.targetOffsets(key, source)
            val changed = (0 until source.size - 20).filter { source[it] != patched[it] }
            assertTrue(changed.isNotEmpty())
            assertTrue(changed.all { offset -> ranges.any { offset in it } })
            assertFailsWith<IllegalArgumentException> { AdGateTransform.patchFeature(patched, key) }
            assertFooter(patched)
        }
        val transforms = buildList<(ByteArray) -> ByteArray> {
            add(AdGateTransform::patch)
            add(AdGateTransform::patchMembership)
            AdGateTransform.featureKeys.forEach { key -> add { AdGateTransform.patchFeature(it, key) } }
            if (AdGateTransform.supportsTarget("daily_bonus", source)) add(AdGateTransform::patchDailyBonus)
        }
        val forward = transforms.fold(source) { bytes, transform -> transform(bytes) }
        val reverse = transforms.reversed().fold(source) { bytes, transform -> transform(bytes) }
        assertContentEquals(forward, reverse)
        assertEquals(source.size, forward.size)
        assertFooter(forward)
        System.getenv("SIMSIMI_PATCHED_HBC")?.let { File(it + ".features").writeBytes(forward) }
    }

    @Test fun membershipAndAdTransformsTouchOnlyTheirReviewedRegions() {
        val source = source()
        val membership = AdGateTransform.patchMembership(source)
        val ad = AdGateTransform.patch(source)
        val membershipRanges = AdGateTransform.targetOffsets("membership", source)
        val adRanges = AdGateTransform.targetOffsets("ads", source)
        val membershipChanges = (0 until source.size - 20).filter { source[it] != membership[it] }
        val adChanges = (0 until source.size - 20).filter { source[it] != ad[it] }
        assertTrue(membershipChanges.isNotEmpty())
        assertTrue(membershipChanges.all { offset -> membershipRanges.any { offset in it } })
        assertTrue(adChanges.isNotEmpty())
        assertTrue(adChanges.all { offset -> adRanges.any { offset in it } })
        assertContentEquals(
            AdGateTransform.patch(AdGateTransform.patchMembership(source)),
            AdGateTransform.patchMembership(AdGateTransform.patch(source))
        )
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patchMembership(membership) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(ad) }
        assertFooter(membership)
        assertFooter(ad)
    }

    @Test fun dailyBonusRemainsFailClosedOnTheChanged926Flow() {
        val source = source()
        if (AdGateTransform.profileVersion(source) == "9.2.3") {
            val daily = AdGateTransform.patchDailyBonus(source)
            assertTrue((0 until source.size - 20).any { source[it] != daily[it] })
            assertFooter(daily)
        } else {
            assertFalse(AdGateTransform.supportsTarget("daily_bonus", source))
            assertFailsWith<IllegalStateException> { AdGateTransform.patchDailyBonus(source) }
        }
    }

    @Test fun rejectsForeignChangesEvenWithARecomputedHermesFooter() {
        val source = source()
        fun changedAt(offset: Int): ByteArray = source.copyOf().also { changed ->
            changed[offset] = (changed[offset].toInt() xor 1).toByte()
            val digest = MessageDigest.getInstance("SHA-1")
            digest.update(changed, 0, changed.size - 20)
            digest.digest().copyInto(changed, changed.size - 20)
        }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(byteArrayOf()) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(ByteArray(source.size)) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(changedAt(100)) }
    }
}
