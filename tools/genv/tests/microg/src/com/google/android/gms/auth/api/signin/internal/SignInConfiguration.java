package com.google.android.gms.auth.api.signin.internal;

import android.os.Parcel;
import android.os.Parcelable;

/**
 * Synthetic parcel for an offline intent-routing test, not GenV code.
 * Only a test package name is included; there are no accounts or tokens.
 * Field 2 uses the public Google SafeParcel format; options are intentionally
 * absent so this cannot authenticate anyone.
 */
public final class SignInConfiguration implements Parcelable {
    private static final int OBJECT_MAGIC = 0x4f45;
    private final String packageName;

    public SignInConfiguration(String packageName) {
        this.packageName = packageName;
    }

    @Override public int describeContents() { return 0; }

    private static int begin(Parcel parcel, int fieldId) {
        parcel.writeInt(0xffff0000 | fieldId);
        parcel.writeInt(0);
        return parcel.dataPosition();
    }

    private static void finish(Parcel parcel, int start) {
        int end = parcel.dataPosition();
        parcel.setDataPosition(start - 4);
        parcel.writeInt(end - start);
        parcel.setDataPosition(end);
    }

    @Override public void writeToParcel(Parcel parcel, int flags) {
        int objectStart = begin(parcel, OBJECT_MAGIC);
        int nameStart = begin(parcel, 2);
        parcel.writeString(packageName);
        finish(parcel, nameStart);
        finish(parcel, objectStart);
    }

    private static int size(Parcel source, int header) {
        return (header & 0xffff0000) == 0xffff0000 ? source.readInt() : header >>> 16;
    }

    public static final Creator<SignInConfiguration> CREATOR = new Creator<SignInConfiguration>() {
        @Override public SignInConfiguration createFromParcel(Parcel source) {
            int header = source.readInt();
            if ((header & 0xffff) != OBJECT_MAGIC) throw new IllegalArgumentException("Invalid object");
            int objectSize = size(source, header);
            int end = source.dataPosition() + objectSize;
            String name = null;
            while (source.dataPosition() < end) {
                int fieldHeader = source.readInt();
                int fieldSize = size(source, fieldHeader);
                int fieldEnd = source.dataPosition() + fieldSize;
                if ((fieldHeader & 0xffff) == 2 && fieldSize > 0) name = source.readString();
                source.setDataPosition(fieldEnd);
            }
            source.setDataPosition(end);
            if (name == null) throw new IllegalArgumentException("Missing package");
            return new SignInConfiguration(name);
        }
        @Override public SignInConfiguration[] newArray(int size) {
            return new SignInConfiguration[size];
        }
    };
}
