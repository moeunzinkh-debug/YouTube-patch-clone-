package app.morphe.patches.simsimi

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest

/** Exact-build composable Hermes transforms; unknown modifications fail closed. */
object AdGateTransform {
    const val ORIGINAL_SHA256 = "203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489"
    const val EXPECTED_SIZE = 26008892
    const val GATE_OFFSET = 17289945 + 0x18f
    const val MEMBERSHIP_OFFSET = 17278582
    const val MEMBERSHIP_EVENTS_OFFSET = 17279803
    const val DAILY_BONUS_OFFSET = 23509822 + 0x13

    const val V926_ORIGINAL_SHA256 = "ae1029cfbc61343b27b8f849a21a50df2b22b2cca361bad8aac1c70f069d8e36"
    const val V926_EXPECTED_SIZE = 26002756

    private val magic = byteArrayOf(0xc6.toByte(), 0x1f, 0xbc.toByte(), 0x03, 0xc1.toByte(), 0x03, 0x19, 0x1f)
    private fun hex(value: String) = value.chunked(2).map { it.toInt(16).toByte() }.toByteArray()

    internal val originalMembership = hex("7c003701000163f27602be0e01023701000207c2510101003701000163f2bda200000001023701000163f236010103887803bc0d01032901012e01010d5c0137020004b1b57901be710201300139040105060036020406b2510202043905010506003701000163f237070107d6c736040508c36a040405080804500105026b0404013701040990f451010104aa2c02013b000301b1b53702000a21c53601000bf25403020001033602030c4c3201640101b71a53010203013700000163f25c002900012e00000d5c00")
    internal val clientMembership = hex("2900012e01000d7c003702000163f23000390300021a0037040303430003055500040305010278013b00010188005c00080000760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600")
    internal val originalMembershipEvents = hex("32017c026c00012a0100002a0101023703020163f27600bc4603003702020163f22a0102022902002e02020037020202f7dd2a0103023003390403031a00360304049a370202050bfb5303030402360203067f640101bf1a53010203015c00")
    internal val clientMembershipEvents = hex("32017c026c00012a0100002a0101023703020185c45103030276000802030802022a0102022902002e02020037020202f7dd2a0103023003390403031a00360304049a370202050bfb5303030402360203067f640101bf1a53010203015c00")

    internal val v926OriginalMembership = hex("7c00370100016df27602be0e01023701000210c251010100370100016df2bda20000000102370100016df236010103877803bc0d01032901012e01010d5c0137020004b8b57901be710201300139040105060036020406b351020204390501050600370100016df237070107dfc736040508c46a040405080804500105026b0404013701040996f451010104aa2c02013b000301b8b53702000a22c53601000bf25403020001033602030c4b3201640101b71a5301020301370000016df25c002900012e00000d5c00")
    internal val v926ClientMembership = hex("2900012e01000d7c00370200016df23000390300021a0037040303420003055500040305010278013b00010187005c00080000760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600760076007600")
    internal val v926OriginalMembershipEvents = hex("32017c026c00012a0100002a010102370302016df27600bc460300370202016df22a0102022902002e02020037020202ffdd2a0103023003390403031a00360304049b370202050cfb5303030402360203067e640101bf1a53010203015c00")
    internal val v926ClientMembershipEvents = hex("32017c026c00012a0100002a0101023703020191c45103030276000802030802022a0102022902002e02020037020202ffdd2a0103023003390403031a00360304049b370202050cfb5303030402360203067e640101bf1a53010203015c00")

    private data class Region(val offset: Int, val original: ByteArray, val replacement: ByteArray) {
        init { require(original.isNotEmpty() && original.size == replacement.size) { "Invalid Hermes patch region" } }
    }
    private data class Profile(
        val version: String,
        val size: Int,
        val sha256: String,
        val targets: Map<String, List<Region>>
    ) {
        val regions = targets.values.flatten().distinctBy { it.offset }
        init {
            require(regions.all { it.offset >= 0 && it.offset + it.original.size <= size - 20 })
            for ((first, second) in regions.sortedBy { it.offset }.zipWithNext()) {
                require(first.offset + first.original.size <= second.offset) { "Overlapping Hermes patch regions" }
            }
        }
    }
    private fun region(offset: Int, original: String, replacement: String) =
        Region(offset, hex(original), hex(replacement))

    private val v923Features = linkedMapOf(
        "conversation_level" to listOf(region(24125135, "3605050166", "7805080505")),
        "profile_photo" to listOf(region(23545009, "2e010909", "78017801")),
        "group_cover" to listOf(region(23207839, "3602020388", "7802080202"), region(23208563, "3605050c88", "7805080505")),
        "photo_send" to listOf(
            region(23919819, "360d000b88", "780d080d0d"), region(25253997, "3602020c88", "7802080202"),
            region(23938312, "2e020105", "78027802"), region(25262480, "2e040307", "78047804")
        ),
        "read_receipts" to listOf(region(23982256, "3601000188", "7801080101")),
        "item_controls" to listOf(region(23121857, "3602000288", "7802080202"), region(23523080, "3602000288", "7802080202"))
    )
    private val v926Features = linkedMapOf(
        "conversation_level" to listOf(region(24120758, "3605050165", "7805080505")),
        "profile_photo" to listOf(region(23541071, "2e010909", "78017801")),
        "group_cover" to listOf(region(23207684, "3602020387", "7802080202"), region(23208408, "3605050c87", "7805080505")),
        "photo_send" to listOf(
            region(23915716, "360c000b87", "780c080c0c"), region(25248710, "3602020c87", "7802080202"),
            region(23934150, "2e020105", "78027802"), region(25257172, "2e040307", "78047804")
        ),
        "read_receipts" to listOf(region(23978078, "3601000187", "7801080101")),
        "item_controls" to listOf(region(23122915, "3602000287", "7802080202"), region(23519138, "3602000287", "7802080202"))
    )
    private val profiles = listOf(
        Profile("9.2.3", EXPECTED_SIZE, ORIGINAL_SHA256, linkedMapOf(
            "ads" to listOf(region(GATE_OFFSET, "78005c00", "79005c00")),
            "membership" to listOf(Region(MEMBERSHIP_OFFSET, originalMembership, clientMembership), Region(MEMBERSHIP_EVENTS_OFFSET, originalMembershipEvents, clientMembershipEvents)),
            "daily_bonus" to listOf(region(DAILY_BONUS_OFFSET, "3701010243f4", "780176017801"))
        ) + v923Features),
        Profile("9.2.6", V926_EXPECTED_SIZE, V926_ORIGINAL_SHA256, linkedMapOf(
            "ads" to listOf(region(17288798, "78005c00", "79005c00")),
            "membership" to listOf(Region(17277342, v926OriginalMembership, v926ClientMembership), Region(17278563, v926OriginalMembershipEvents, v926ClientMembershipEvents))
        ) + v926Features)
    )

    internal val featureKeys get() = v923Features.keys.toList()
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
    private fun checksum(bytes: ByteArray): ByteArray = MessageDigest.getInstance("SHA-1").run {
        update(bytes, 0, bytes.size - 20)
        digest()
    }
    private fun validateHeader(original: ByteArray) {
        require(original.size > 40 && original.copyOfRange(0, 8).contentEquals(magic)) { "Not a Hermes payload" }
        val header = ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN)
        require(header.getInt(8) == 96 && header.getInt(32) == original.size) { "Unsupported Hermes header" }
        require(checksum(original).contentEquals(original.copyOfRange(original.size - 20, original.size))) { "Hermes checksum mismatch" }
    }
    private fun resolve(original: ByteArray): Pair<Profile, ByteArray> {
        validateHeader(original)
        val candidates = profiles.filter { it.size == original.size }
        require(candidates.isNotEmpty()) { "Unsupported SimSimi Hermes payload size" }
        for (profile in candidates) {
            val normalized = original.copyOf()
            if (profile.regions.any { region ->
                    val actual = original.copyOfRange(region.offset, region.offset + region.original.size)
                    !actual.contentEquals(region.original) && !actual.contentEquals(region.replacement)
                }) continue
            profile.regions.forEach { it.original.copyInto(normalized, it.offset) }
            checksum(normalized).copyInto(normalized, normalized.size - 20)
            if (sha256(normalized) == profile.sha256) return profile to normalized
        }
        throw IllegalArgumentException("Unsupported SimSimi payload; unknown changes detected")
    }
    private fun apply(original: ByteArray, key: String): ByteArray {
        val (profile, normalized) = resolve(original)
        val targets = profile.targets[key] ?: error("$key is unavailable for SimSimi ${profile.version}")
        require(targets.all { target ->
            original.copyOfRange(target.offset, target.offset + target.original.size).contentEquals(target.original)
        }) { "Patch is already applied" }
        profile.regions.forEach { region ->
            original.copyInto(normalized, region.offset, region.offset, region.offset + region.original.size)
        }
        targets.forEach { it.replacement.copyInto(normalized, it.offset) }
        checksum(normalized).copyInto(normalized, normalized.size - 20)
        return normalized
    }

    fun patch(original: ByteArray): ByteArray = apply(original, "ads")
    fun patchMembership(original: ByteArray): ByteArray = apply(original, "membership")
    fun patchDailyBonus(original: ByteArray): ByteArray =
        if (supportsTarget("daily_bonus", original)) apply(original, "daily_bonus") else original.copyOf()
    fun patchFeature(original: ByteArray, feature: String): ByteArray = apply(original, feature)
    internal fun featureOffsets(feature: String): List<IntRange> = v923Features.getValue(feature).map {
        it.offset until it.offset + it.original.size
    }
    internal fun targetOffsets(key: String, original: ByteArray): List<IntRange> {
        val profile = resolve(original).first
        return profile.targets.getValue(key).map { it.offset until it.offset + it.original.size }
    }
    internal fun profileVersion(original: ByteArray): String = resolve(original).first.version
    internal fun supportsTarget(key: String, original: ByteArray): Boolean = key in resolve(original).first.targets
}
