package app.morphe.patches.simsimi

import java.io.File
import java.security.MessageDigest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class AdGateTransformTest {
    @Test fun dailyBonusUsesExistingNonVideoFlowAndComposesInEveryOrder() {
        val source = File(System.getenv("SIMSIMI_HBC_FIXTURE") ?: error("Exact fixture required")).readBytes()
        val daily = AdGateTransform.patchDailyBonus(source)
        val offset = AdGateTransform.DAILY_BONUS_OFFSET
        assertContentEquals(byteArrayOf(120,1,118,1,120,1), daily.copyOfRange(offset,offset+6))
        assertTrue((0 until source.size-20).filter { source[it] != daily[it] }.all { it in offset until offset+6 })
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patchDailyBonus(daily) }
        val transforms: List<(ByteArray) -> ByteArray> = listOf(AdGateTransform::patch, AdGateTransform::patchMembership, AdGateTransform::patchDailyBonus)
        val expected = transforms.fold(source) { bytes, transform -> transform(bytes) }
        for (order in listOf(listOf(0,1,2),listOf(0,2,1),listOf(1,0,2),listOf(1,2,0),listOf(2,0,1),listOf(2,1,0))) {
            assertContentEquals(expected, order.fold(source) { bytes, index -> transforms[index](bytes) })
        }
        assertEquals(source.size, expected.size)
        assertContentEquals(MessageDigest.getInstance("SHA-1").digest(expected.copyOfRange(0, expected.size-20)), expected.copyOfRange(expected.size-20,expected.size))
        System.getenv("SIMSIMI_PATCHED_HBC")?.let { File(it+".all").writeBytes(expected) }
    }
    @Test fun membershipIsComposableAndDoesNotRewriteOtherCode() {
        val source = File(System.getenv("SIMSIMI_HBC_FIXTURE") ?: error("Exact fixture required")).readBytes()
        val membership = AdGateTransform.patchMembership(source)
        val both = AdGateTransform.patch(membership)
        assertContentEquals(both, AdGateTransform.patchMembership(AdGateTransform.patch(source)))
        assertContentEquals(AdGateTransform.clientMembership, membership.copyOfRange(AdGateTransform.MEMBERSHIP_OFFSET, AdGateTransform.MEMBERSHIP_OFFSET+201))
        assertContentEquals(AdGateTransform.clientMembershipEvents, membership.copyOfRange(AdGateTransform.MEMBERSHIP_EVENTS_OFFSET, AdGateTransform.MEMBERSHIP_EVENTS_OFFSET+95))
        assertEquals(source.size, both.size)
        val changed = (0 until source.size-20).filter { source[it] != both[it] }
        assertTrue(changed.all { it == AdGateTransform.GATE_OFFSET || it in AdGateTransform.MEMBERSHIP_OFFSET until AdGateTransform.MEMBERSHIP_OFFSET+201 || it in AdGateTransform.MEMBERSHIP_EVENTS_OFFSET until AdGateTransform.MEMBERSHIP_EVENTS_OFFSET+95 })
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patchMembership(membership) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(both) }
        System.getenv("SIMSIMI_PATCHED_HBC")?.let { File(it+".combined").writeBytes(both) }
    }
    @Test fun rejectsUnexpectedPayload() {
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(byteArrayOf()) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(ByteArray(AdGateTransform.EXPECTED_SIZE)) }
    }
    @Test fun patchesExactUploadedPayloadWithoutMovingOffsets() {
        val fixture = System.getenv("SIMSIMI_HBC_FIXTURE") ?: error("Exact APK fixture is required in CI")
        val source = File(fixture).readBytes()
        val pristine = source.copyOf()
        val patched = AdGateTransform.patch(source)
        assertContentEquals(pristine, source)
        assertEquals(source.size, patched.size)
        assertEquals(121, patched[AdGateTransform.GATE_OFFSET].toInt())
        val end = source.size - 20
        val changed = (0 until end).filter { source[it] != patched[it] }
        assertEquals(listOf(AdGateTransform.GATE_OFFSET), changed)
        assertContentEquals(MessageDigest.getInstance("SHA-1").digest(patched.copyOfRange(0, end)), patched.copyOfRange(end, patched.size))
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(patched) }
        assertFailsWith<IllegalArgumentException> { AdGateTransform.patch(source.copyOf().also { it[100] = (it[100].toInt() xor 1).toByte() }) }
        assertTrue(AdGateTransform.sha256(patched) != AdGateTransform.ORIGINAL_SHA256)
        System.getenv("SIMSIMI_PATCHED_HBC")?.let { File(it).writeBytes(patched) }
    }
}
