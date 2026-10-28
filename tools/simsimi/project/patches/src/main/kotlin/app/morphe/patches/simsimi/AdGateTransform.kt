package app.morphe.patches.simsimi

import java.security.MessageDigest
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Exact-build composable Hermes transforms; unknown modifications fail closed. */
object AdGateTransform {
    const val ORIGINAL_SHA256 = "203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489"
    const val EXPECTED_SIZE = 26008892
    const val GATE_OFFSET = 17289945 + 0x18f
    const val MEMBERSHIP_OFFSET = 17278582
    private val magic = byteArrayOf(0xc6.toByte(), 0x1f, 0xbc.toByte(), 0x03, 0xc1.toByte(), 0x03, 0x19, 0x1f)
    private fun hex(value: String) = value.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    internal val originalMembership = hex("7c003701000163f27602be0e01023701000207c2510101003701000163f2bda200000001023701000163f236010103887803bc0d01032901012e01010d5c0137020004b1b57901be710201300139040105060036020406b2510202043905010506003701000163f237070107d6c736040508c36a040405080804500105026b0404013701040990f451010104aa2c02013b000301b1b53702000a21c53601000bf25403020001033602030c4c3201640101b71a53010203013700000163f25c002900012e00000d5c00")
    // Hermes 96 function #6838, frameSize 15, no exception handler.
    // Read default and current status, clone with Object.assign({}, default, current),
    // then put hasMembership=true on the CLONE. Preserve other fields and stored state.
    // Object id=26, assign id=67, currentMembershipStatus id=62051, hasMembership id=136.
    internal val clientMembership = hex("2900012e01000d7c003702000163f23000390300021a0037040303430003055500040305010278013b00010188005c00080000760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600")
    private data class Region(val offset: Int, val original: ByteArray, val replacement: ByteArray)
    private val ads = Region(GATE_OFFSET, byteArrayOf(120,0,92,0), byteArrayOf(121,0,92,0))
    private val membership = Region(MEMBERSHIP_OFFSET, originalMembership, clientMembership)
    private val regions = listOf(ads, membership)
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
    private fun checksum(bytes: ByteArray) = MessageDigest.getInstance("SHA-1").digest(bytes.copyOfRange(0, bytes.size-20))
    private fun apply(original: ByteArray, target: Region): ByteArray {
        require(original.size == EXPECTED_SIZE) { "Unsupported SimSimi Hermes payload size" }
        require(original.copyOfRange(0,8).contentEquals(magic)) { "Not a Hermes payload" }
        val header = ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN)
        require(header.getInt(8)==96 && header.getInt(32)==original.size) { "Unsupported Hermes header" }
        require(checksum(original).contentEquals(original.copyOfRange(original.size-20,original.size))) { "Hermes checksum mismatch" }
        val normalized = original.copyOf()
        for (region in regions) {
            val actual = original.copyOfRange(region.offset,region.offset+region.original.size)
            require(actual.contentEquals(region.original) || actual.contentEquals(region.replacement)) { "Unsupported SimSimi patch region" }
            region.original.copyInto(normalized,region.offset)
        }
        checksum(normalized).copyInto(normalized,normalized.size-20)
        require(sha256(normalized)==ORIGINAL_SHA256) { "Unsupported SimSimi payload; unknown changes detected" }
        require(original.copyOfRange(target.offset,target.offset+target.original.size).contentEquals(target.original)) { "Patch is already applied" }
        return original.copyOf().also {
            target.replacement.copyInto(it,target.offset)
            checksum(it).copyInto(it,it.size-20)
        }
    }
    fun patch(original: ByteArray): ByteArray = apply(original,ads)
    fun patchMembership(original: ByteArray): ByteArray = apply(original,membership)
}
