package app.morphe.patches.simsimi

import java.security.MessageDigest
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Exact-build, size-preserving Hermes transformation. Does not grant membership/rewards. */
object AdGateTransform {
    const val ORIGINAL_SHA256 = "203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489"
    const val EXPECTED_SIZE = 26008892
    // Hermes function #6882 canShowAds, offset 17289945, size 403.
    // Change its final LoadConstTrue r0; Ret r0 into LoadConstFalse r0; Ret r0.
    const val GATE_OFFSET = 17289945 + 0x18f
    private val magic = byteArrayOf(0xc6.toByte(), 0x1f, 0xbc.toByte(), 0x03, 0xc1.toByte(), 0x03, 0x19, 0x1f)
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }

    fun patch(original: ByteArray): ByteArray {
        require(original.size == EXPECTED_SIZE) { "Unsupported SimSimi Hermes payload size" }
        require(sha256(original) == ORIGINAL_SHA256) { "Unsupported or already modified SimSimi 9.2.3 payload" }
        require(original.copyOfRange(0, 8).contentEquals(magic)) { "Not a Hermes payload" }
        require(ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN).getInt(8) == 96) { "Hermes version must be 96" }
        require(ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN).getInt(32) == original.size) { "Invalid Hermes file length" }
        require(original.copyOfRange(GATE_OFFSET, GATE_OFFSET + 4).contentEquals(byteArrayOf(120, 0, 92, 0))) {
            "Ad eligibility return fingerprint does not match"
        }
        val end = original.size - 20
        require(MessageDigest.getInstance("SHA-1").digest(original.copyOfRange(0, end))
            .contentEquals(original.copyOfRange(end, original.size))) { "Original Hermes checksum mismatch" }
        return original.copyOf().also { patched ->
            patched[GATE_OFFSET] = 121 // Hermes 96 LoadConstFalse; keep r0 and Ret r0 intact.
            MessageDigest.getInstance("SHA-1").digest(patched.copyOfRange(0, end)).copyInto(patched, end)
        }
    }
}
