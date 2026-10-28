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
    private data class Region(val offset: Int, val original: ByteArray, val replacement: ByteArray) {
        init {
            require(original.isNotEmpty() && original.size == replacement.size) { "Invalid Hermes patch region" }
            require(offset >= 0 && offset + original.size <= EXPECTED_SIZE - 20) { "Hermes patch region out of range" }
        }
    }
    private val ads = Region(GATE_OFFSET, byteArrayOf(120,0,92,0), byteArrayOf(121,0,92,0))
    private val membership = Region(MEMBERSHIP_OFFSET, originalMembership, clientMembership)
    // #22097: replace only the membershipStatus read with true/undefined/true
    // in the same register (three valid 2-byte instructions, no offsets moved).
    // Existing loadMembershipAdmob still fetches server state and preserves errors.
    const val DAILY_BONUS_OFFSET = 23509822 + 0x13
    private val dailyBonus = Region(DAILY_BONUS_OFFSET, hex("3701010243f4"), hex("780176017801"))
    // Live listeners must receive the same cloned UI status as initial reads.
    // The original getter-only patch could be overwritten by a server update.
    const val MEMBERSHIP_EVENTS_OFFSET = 17279803
    internal val originalMembershipEvents = hex("32017c026c00012a0100002a0101023703020163f27600bc4603003702020163f22a0102022902002e02020037020202f7dd2a0103023003390403031a00360304049a370202050bfb5303030402360203067f640101bf1a53010203015c00")
    internal val clientMembershipEvents = hex("32017c026c00012a0100002a0101023703020185c45103030276000802030802022a0102022902002e02020037020202f7dd2a0103023003390403031a00360304049a370202050bfb5303030402360203067f640101bf1a53010203015c00")
    private val membershipEvents = Region(MEMBERSHIP_EVENTS_OFFSET, originalMembershipEvents, clientMembershipEvents)
    // Exact feature-entry gates, not fabricated server balances or message read state.
    private val featureRegions = linkedMapOf(
        "conversation_level" to listOf(Region(24125135, hex("3605050166"), hex("7805080505"))),
        "profile_photo" to listOf(Region(23545009, hex("2e010909"), hex("78017801"))),
        "group_cover" to listOf(Region(23207839, hex("3602020388"), hex("7802080202")), Region(23208563, hex("3605050c88"), hex("7805080505"))),
        // Keep both composer state and the actual send callbacks on the existing
        // member path; preserve upload, response handling and server enforcement.
        "photo_send" to listOf(
            Region(23919819, hex("360d000b88"), hex("780d080d0d")),
            Region(25253997, hex("3602020c88"), hex("7802080202")),
            Region(23938312, hex("2e020105"), hex("78027802")),
            Region(25262480, hex("2e040307"), hex("78047804"))
        ),
        "read_receipts" to listOf(Region(23982256, hex("3601000188"), hex("7801080101"))),
        "item_controls" to listOf(Region(23121857, hex("3602000288"), hex("7802080202")), Region(23523080, hex("3602000288"), hex("7802080202")))
    )
    internal val featureKeys get() = featureRegions.keys.toList()
    private val regions = listOf(ads, membership, dailyBonus, membershipEvents) + featureRegions.values.flatten()
    init {
        for ((first, second) in regions.sortedBy { it.offset }.zipWithNext()) {
            require(first.offset+first.original.size <= second.offset) { "Overlapping Hermes patch regions" }
        }
    }
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
    // Stream the 26 MB input instead of allocating another full-size copy on
    // Android each time the user selects one of the composable feature patches.
    private fun checksum(bytes: ByteArray): ByteArray = MessageDigest.getInstance("SHA-1").run {
        update(bytes, 0, bytes.size-20)
        digest()
    }
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
        // Reuse the validated buffer, restoring all previously selected regions
        // from the input before adding this one. Avoid a third full HBC buffer.
        for (region in regions) {
            original.copyInto(normalized, region.offset, region.offset, region.offset+region.original.size)
        }
        target.replacement.copyInto(normalized,target.offset)
        checksum(normalized).copyInto(normalized,normalized.size-20)
        return normalized
    }
    fun patch(original: ByteArray): ByteArray = apply(original,ads)
    fun patchMembership(original: ByteArray): ByteArray = apply(apply(original,membership),membershipEvents)
    fun patchDailyBonus(original: ByteArray): ByteArray = apply(original,dailyBonus)
    fun patchFeature(original: ByteArray, feature: String): ByteArray =
        featureRegions.getValue(feature).fold(original) { bytes, region -> apply(bytes,region) }
    internal fun featureOffsets(feature: String): List<IntRange> = featureRegions.getValue(feature).map {
        it.offset until it.offset+it.original.size
    }
}
