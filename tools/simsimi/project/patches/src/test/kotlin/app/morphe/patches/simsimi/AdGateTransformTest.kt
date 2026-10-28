package app.morphe.patches.simsimi

import java.io.File
import java.security.MessageDigest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class AdGateTransformTest {
    @Test fun membershipIsComposableAndDoesNotRewriteOtherCode() {
        val source = File(System.getenv("SIMSIMI_HBC_FIXTURE") ?: error("Exact fixture required")).readBytes()
        val membership = AdGateTransform.patchMembership(source)
        val both = AdGateTransform.patch(membership)
        assertContentEquals(both, AdGateTransform.patchMembership(AdGateTransform.patch(source)))
        assertContentEquals(AdGateTransform.clientMembership, membership.copyOfRange(AdGateTransform.MEMBERSHIP_OFFSET, AdGateTransform.MEMBERSHIP_OFFSET+201))
        assertEquals(source.size, both.size)
        val changed = (0 until source.size-20).filter { source[it] != both[it] }
        assertTrue(changed.all { it == AdGateTransform.GATE_OFFSET || it in AdGateTransform.MEMBERSHIP_OFFSET until AdGateTransform.MEMBERSHIP_OFFSET+201 })
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
