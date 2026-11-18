package app.morphe.patches.genv

import java.io.ByteArrayInputStream
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import org.w3c.dom.Document

class RemoveAdsManifestTest {
    private fun document(extra: String = ""): Document {
        val xml = """
            <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.ainate.ai.video.generate">
              <uses-permission android:name="android.permission.INTERNET"/>
              <uses-permission android:name="android.permission.ACCESS_ADSERVICES_AD_ID"/>
              <uses-permission android:name="com.google.android.gms.permission.AD_ID"/>
              <uses-permission android:name="com.android.vending.BILLING"/>
              <application>
                <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="@string/admob_app_id"/>
                <meta-data android:name="firebase_data_collection_default_enabled" android:value="true"/>
                $extra
              </application>
            </manifest>
        """.trimIndent()
        return DocumentBuilderFactory.newInstance().apply { isNamespaceAware = true }
            .newDocumentBuilder().parse(ByteArrayInputStream(xml.toByteArray()))
    }

    private fun names(document: Document, tag: String): List<String> {
        val nodes = document.getElementsByTagName(tag)
        return (0 until nodes.length).map {
            nodes.item(it).attributes.getNamedItemNS("http://schemas.android.com/apk/res/android", "name")?.nodeValue.orEmpty()
        }
    }

    @Test fun removesOnlyAdMobMetadataAndAdvertisingIdentifiers() {
        val document = document()
        removeAdvertisingManifestEntries(document)
        assertEquals(listOf("android.permission.INTERNET", "com.android.vending.BILLING"), names(document, "uses-permission"))
        assertEquals(listOf("firebase_data_collection_default_enabled"), names(document, "meta-data"))
    }

    @Test fun failsClosedWhenReviewedInputsChange() {
        val missingPermission = document().also {
            val permissions = it.getElementsByTagName("uses-permission")
            val node = (0 until permissions.length).map { index -> permissions.item(index) }
                .single { item -> item.attributes.getNamedItemNS("http://schemas.android.com/apk/res/android", "name").nodeValue == "com.google.android.gms.permission.AD_ID" }
            node.parentNode.removeChild(node)
        }
        assertFailsWith<IllegalArgumentException> { removeAdvertisingManifestEntries(missingPermission) }
        assertFailsWith<IllegalArgumentException> {
            removeAdvertisingManifestEntries(document("<meta-data android:name=\"com.google.android.gms.ads.APPLICATION_ID\" android:value=\"duplicate\"/>"))
        }
    }

    @Test fun neverTouchesBillingOrEntitlementMetadata() {
        val document = document("<meta-data android:name=\"server_entitlement_required\" android:value=\"true\"/>")
        removeAdvertisingManifestEntries(document)
        assertTrue("com.android.vending.BILLING" in names(document, "uses-permission"))
        assertTrue("server_entitlement_required" in names(document, "meta-data"))
    }
}
